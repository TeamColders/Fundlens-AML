import os
import json
import time
from confluent_kafka import Producer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC = "transactions.raw"

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def stream_transactions():
    """
    Reads synthetic transactions from JSON and streams them to Kafka.
    Simulates a Core Banking System (CBS) real-time feed.
    """
    print(f"Connecting to Kafka broker at {KAFKA_BROKER}...")
    producer = Producer({'bootstrap.servers': KAFKA_BROKER})
    
    file_path = "data/synthetic/transactions.json"
    if not os.path.exists(file_path):
        print(f"Error: Could not find {file_path}")
        return

    with open(file_path, 'r') as f:
        transactions = json.load(f)
        
    print(f"Loaded {len(transactions)} transactions. Beginning stream...")
    
    for i, txn in enumerate(transactions):
        # Trigger any available delivery report callbacks from previous produce() calls
        producer.poll(0)
        
        # Asynchronously produce a message. The routing key is the sender account to ensure ordering.
        producer.produce(
            TOPIC, 
            key=txn.get("sender_account", "UNKNOWN").encode('utf-8'),
            value=json.dumps(txn).encode('utf-8'), 
            callback=delivery_report
        )
        
        # Simulate real-time delay (e.g., 1 transaction per second for demo)
        # time.sleep(1)
        
        # To just blast it in, we'll sleep a tiny bit
        time.sleep(0.01)

    # Wait for any outstanding messages to be delivered and delivery report callbacks to be triggered
    producer.flush()
    print("Stream complete.")

if __name__ == "__main__":
    stream_transactions()
