import os
import json
import asyncio
from confluent_kafka import Consumer
from backend.ml.gnn_model import FraudGAT
import torch

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
IN_TOPIC = "transactions.enriched"

# Initialize GNN model globally
model = FraudGAT()
try:
    model.load_state_dict(torch.load("fundlens_gnn.pt"))
    print("Loaded trained GNN model.")
except Exception as e:
    print(f"Could not load trained model, using untrained weights: {e}")
model.eval()

def score_transaction(enriched_data):
    """
    Format the enriched data as a mini-subgraph and pass it to the GNN.
    """
    raw_txn = enriched_data["transaction"]
    features = enriched_data["features"]
    
    sender_id = raw_txn.get("sender_account")
    receiver_id = raw_txn.get("receiver_account")
    
    # Construct mini-subgraph
    nodes = [
        {"account_id": sender_id, "features": features["sender_node"]},
        {"account_id": receiver_id, "features": features["receiver_node"]}
    ]
    edges = [
        {"source": sender_id, "target": receiver_id, "features": features["edge"]}
    ]
    
    predictions = model.predict_subgraph(nodes, edges)
    # Return the max risk score among the involved nodes
    risk_score = max(predictions.values()) if predictions else 0.0
    return risk_score

async def run_alert_pipeline():
    print(f"Starting Alert Pipeline... Listening on {IN_TOPIC}")
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'alert-pipeline-group',
        'auto.offset.reset': 'earliest'
    })
    
    consumer.subscribe([IN_TOPIC])
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                await asyncio.sleep(0.1)
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
                
            enriched_data = json.loads(msg.value().decode('utf-8'))
            
            # Run GNN scoring
            risk_score = score_transaction(enriched_data)
            
            # If high risk, theoretically trigger WebSocket/DB insert
            if risk_score > 0.8:
                raw = enriched_data["transaction"]
                print(f"🚨 ALERT: High Risk Transaction ({risk_score:.2f})!")
                print(f"   {raw.get('sender_account')} -> {raw.get('receiver_account')} (Amt: {raw.get('amount')})")
                
            # Yield control to event loop
            await asyncio.sleep(0)
            
    except KeyboardInterrupt:
        print("Alert pipeline stopped.")
    finally:
        consumer.close()

if __name__ == "__main__":
    asyncio.run(run_alert_pipeline())
