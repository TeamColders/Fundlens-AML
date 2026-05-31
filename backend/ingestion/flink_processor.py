import os
import json
from collections import defaultdict
from confluent_kafka import Consumer, Producer
from backend.ml.feature_extractor import extract_node_features, extract_edge_features

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
IN_TOPIC = "transactions.raw"
OUT_TOPIC = "transactions.enriched"

# Simple in-memory state to mock Flink's keyed state
# In production, Flink handles this durably.
account_state = defaultdict(lambda: {
    "velocity_24h": 0.0,
    "velocity_7d": 0.0,
    "historical_avg_amount": 1000.0,
    "counterparty_entropy": 0.5,
    "inbound_ratio": 0.5,
    "deviation_from_baseline": 0.0,
    "time_since_last_txn_norm": 1.0,
    "is_new_counterparty": 1.0,
    "sender_historical_avg": 1000.0
})

def start_processor():
    print(f"Starting simulated Flink processor... Connecting to {KAFKA_BROKER}")
    
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'flink-processor-group',
        'auto.offset.reset': 'earliest'
    })
    
    producer = Producer({'bootstrap.servers': KAFKA_BROKER})
    
    consumer.subscribe([IN_TOPIC])
    
    print(f"Listening on {IN_TOPIC} and outputting to {OUT_TOPIC}")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            
            raw_txn = json.loads(msg.value().decode('utf-8'))
            sender = raw_txn.get("sender_account")
            receiver = raw_txn.get("receiver_account")
            amount = raw_txn.get("amount", 0.0)
            
            # --- Stateful Processing (Mocking Flink window aggregation) ---
            s_state = account_state[sender]
            r_state = account_state[receiver]
            
            # Update sender state (velocity mock)
            s_state["velocity_24h"] += amount
            s_state["velocity_7d"] += amount
            
            # Calculate features
            sender_node_features = extract_node_features({"account_id": sender}, s_state)
            receiver_node_features = extract_node_features({"account_id": receiver}, r_state)
            edge_features = extract_edge_features(raw_txn, s_state)
            
            enriched_txn = {
                "transaction": raw_txn,
                "features": {
                    "sender_node": sender_node_features,
                    "receiver_node": receiver_node_features,
                    "edge": edge_features
                }
            }
            
            # Publish enriched transaction
            producer.produce(
                OUT_TOPIC,
                key=sender.encode('utf-8') if sender else b'',
                value=json.dumps(enriched_txn).encode('utf-8')
            )
            producer.poll(0)

    except KeyboardInterrupt:
        print("Processor stopped by user.")
    finally:
        consumer.close()
        producer.flush()

if __name__ == "__main__":
    start_processor()
