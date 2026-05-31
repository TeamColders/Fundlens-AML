import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def generate_transactions(total_count=10000):
    clean_count = int(total_count * 0.9)
    fraud_count = total_count - clean_count

    # Distribute fraud count evenly across 5 typologies
    typology_counts = {
        "round_trip_layering": fraud_count // 5,
        "structuring": fraud_count // 5,
        "dormant_activation": fraud_count // 5,
        "fan_out_fan_in": fraud_count // 5,
        "mule_chain": fraud_count // 5,
    }
    # Adjust last one to ensure exact total if not divisible
    typology_counts["mule_chain"] += fraud_count - sum(typology_counts.values())

    transactions = []
    
    start_date = datetime.now() - timedelta(days=30)
    channels = ['NEFT', 'UPI', 'IMPS', 'RTGS', 'CARD']
    channel_weights = [0.40, 0.30, 0.15, 0.10, 0.05]

    def make_txn(sender, receiver, amount, timestamp, is_fraud=False, typology=None):
        return {
            "transaction_id": f"TXN-{uuid.uuid4().hex[:12].upper()}",
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": round(amount, 2),
            "currency": "INR",
            "timestamp": timestamp.isoformat(),
            "channel": random.choices(channels, weights=channel_weights)[0],
            "branch_code": f"BR-{random.randint(100, 999)}",
            "reference_number": f"REF-{random.randint(100000, 999999)}",
            "is_fraud": is_fraud,
            "typology": typology
        }

    # Helper to generate random accounts
    def get_account():
        return f"ACC-{random.randint(1000, 9999)}"

    print("Generating clean transactions...")
    for _ in range(clean_count):
        sender = get_account()
        receiver = get_account()
        while receiver == sender:
            receiver = get_account()
        
        # log-normal distribution, numpy expects log-mean and log-sigma
        # mean=50000, roughly e^10.82
        amount = np.random.lognormal(mean=10.8, sigma=1.5)
        # Cap reasonable extremes
        amount = max(100, min(amount, 5000000))
        
        timestamp = start_date + timedelta(seconds=random.randint(0, 30 * 24 * 3600))
        transactions.append(make_txn(sender, receiver, amount, timestamp))

    print("Generating round-trip layering...")
    for _ in range(typology_counts["round_trip_layering"]):
        A = get_account()
        B, C, D = get_account(), get_account(), get_account()
        E = get_account()
        
        total_amount = random.uniform(2000000, 10000000) # 20L to 1Cr
        amount_B = total_amount * random.uniform(0.2, 0.4)
        amount_C = total_amount * random.uniform(0.2, 0.4)
        amount_D = total_amount - amount_B - amount_C
        
        base_time = start_date + timedelta(seconds=random.randint(0, 29 * 24 * 3600))
        
        # Split A -> B, C, D
        transactions.append(make_txn(A, B, amount_B, base_time, True, "round_trip_layering"))
        transactions.append(make_txn(A, C, amount_C, base_time + timedelta(minutes=random.randint(10, 60)), True, "round_trip_layering"))
        transactions.append(make_txn(A, D, amount_D, base_time + timedelta(minutes=random.randint(10, 60)), True, "round_trip_layering"))
        
        # Consolidate B, C, D -> E
        mid_time = base_time + timedelta(hours=random.randint(2, 5))
        transactions.append(make_txn(B, E, amount_B, mid_time + timedelta(minutes=random.randint(10, 60)), True, "round_trip_layering"))
        transactions.append(make_txn(C, E, amount_C, mid_time + timedelta(minutes=random.randint(10, 60)), True, "round_trip_layering"))
        transactions.append(make_txn(D, E, amount_D, mid_time + timedelta(minutes=random.randint(10, 60)), True, "round_trip_layering"))
        
        # E -> A
        final_time = base_time + timedelta(hours=random.randint(6, 12))
        transactions.append(make_txn(E, A, total_amount, final_time, True, "round_trip_layering"))

    print("Generating structuring...")
    for _ in range(typology_counts["structuring"]):
        source = get_account()
        num_transfers = random.randint(8, 15)
        base_time = start_date + timedelta(seconds=random.randint(0, 27 * 24 * 3600))
        
        for i in range(num_transfers):
            amount = random.uniform(150000, 190000) # Just below 2L
            timestamp = base_time + timedelta(hours=(72 / num_transfers) * i)
            transactions.append(make_txn(source, get_account(), amount, timestamp, True, "structuring"))

    print("Generating dormant account activation...")
    for _ in range(typology_counts["dormant_activation"]):
        dormant_account = get_account()
        base_time = start_date + timedelta(seconds=random.randint(0, 28 * 24 * 3600))
        
        inward_amount = random.uniform(500000, 2000000) # > 5L
        transactions.append(make_txn(get_account(), dormant_account, inward_amount, base_time, True, "dormant_activation"))
        
        outward_time = base_time + timedelta(hours=random.randint(1, 48))
        transactions.append(make_txn(dormant_account, get_account(), inward_amount, outward_time, True, "dormant_activation"))

    print("Generating fan-out fan-in...")
    for _ in range(typology_counts["fan_out_fan_in"]):
        source = get_account()
        destination = get_account()
        num_intermediaries = random.randint(5, 10)
        intermediaries = [get_account() for _ in range(num_intermediaries)]
        
        total_amount = random.uniform(1000000, 5000000)
        base_time = start_date + timedelta(seconds=random.randint(0, 28 * 24 * 3600))
        
        amounts = []
        rem = total_amount
        for i in range(num_intermediaries - 1):
            amt = rem * random.uniform(0.1, 1.5 / num_intermediaries)
            amounts.append(amt)
            rem -= amt
        amounts.append(rem)
        
        # Fan out
        for i, inter in enumerate(intermediaries):
            t = base_time + timedelta(minutes=random.randint(5, 120))
            transactions.append(make_txn(source, inter, amounts[i], t, True, "fan_out_fan_in"))
            
        # Fan in
        for i, inter in enumerate(intermediaries):
            t = base_time + timedelta(hours=random.randint(12, 24))
            transactions.append(make_txn(inter, destination, amounts[i], t, True, "fan_out_fan_in"))

    print("Generating mule chain...")
    for _ in range(typology_counts["mule_chain"]):
        accounts = [get_account() for _ in range(5)] # A -> B -> C -> D -> E
        amount = random.uniform(500000, 2000000)
        base_time = start_date + timedelta(seconds=random.randint(0, 29 * 24 * 3600))
        
        for i in range(4):
            sender = accounts[i]
            receiver = accounts[i+1]
            t = base_time + timedelta(hours=3*i + random.uniform(0, 2)) # Completed within 12 hours
            transactions.append(make_txn(sender, receiver, amount, t, True, "mule_chain"))
            amount = amount * random.uniform(0.95, 0.98) # 2-5% skimmed

    # Note: total count may slightly exceed total_count due to how typologies are structured (each adds multiple txns)
    # But this is fine for training. We'll shuffle and return.
    random.shuffle(transactions)
    df = pd.DataFrame(transactions)
    print(f"Generated {len(df)} transactions total.")
    return df

if __name__ == "__main__":
    import os
    import json
    
    os.makedirs('data/synthetic', exist_ok=True)
    df = generate_transactions(10000)
    
    # Save as CSV
    df.to_csv('data/synthetic/transactions.csv', index=False)
    
    # Also save as JSON for ML train compatibility (gnn_train.py expects subgraphs, but let's provide a raw json too)
    df.to_json('data/synthetic/raw_transactions.json', orient='records', lines=True)
    print("Saved to data/synthetic/transactions.csv and raw_transactions.json")
