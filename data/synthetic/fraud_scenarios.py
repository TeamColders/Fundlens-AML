"""
Synthetic banking transaction data generator for AML fraud detection.
Generates 10,000 transactions with 90% clean and 10% fraud patterns.

Fraud typologies implemented:
1. Round-trip layering
2. Structuring / Smurfing
3. Dormant account activation
4. Fan-out fan-in
5. Mule chain
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import random


class FraudScenarioGenerator:
    def __init__(self, seed: int = 42, base_date: datetime = None):
        """Initialize fraud scenario generator."""
        random.seed(seed)
        np.random.seed(seed)
        self.base_date = base_date or datetime(2024, 1, 1)
        self.transactions = []
        self.next_txn_id = 1
        self.account_pool = self._generate_account_pool()
        self.entity_map = {}

    def _generate_account_pool(self) -> List[str]:
        """Generate realistic account IDs."""
        return [f"ACC-{i:04d}" for i in range(500)]

    def _get_or_create_entity(self, account_id: str) -> str:
        """Get or create entity ID for account."""
        if account_id not in self.entity_map:
            entity_id = f"ENT-{len(self.entity_map):05d}"
            self.entity_map[account_id] = entity_id
        return self.entity_map[account_id]

    def _generate_account_metadata(self, account_id: str) -> Dict:
        """Generate metadata for an account."""
        return {
            "account_id": account_id,
            "account_type": random.choice(["savings", "current", "nri"]),
            "kyc_tier": random.choice([1, 2, 3]),
            "created_date": self.base_date - timedelta(days=random.randint(30, 1825)),
            "status": "active",
            "is_dormant": random.random() < 0.05,  # 5% dormant
            "declared_income": np.random.lognormal(10.5, 1.2),  # Log-normal distribution
        }

    def _add_transaction(
        self,
        sender: str,
        receiver: str,
        amount: float,
        timestamp: datetime,
        channel: str,
        is_fraud: bool = False,
        typology: str = None,
        case_id: str = None,
    ) -> Dict:
        """Add transaction to list."""
        txn = {
            "transaction_id": f"TXN-{self.next_txn_id:08d}",
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": amount,
            "currency": "INR",
            "timestamp": timestamp,
            "channel": channel,
            "branch_code": f"BR{random.randint(100, 999)}",
            "reference_number": f"REF-{random.randint(1000000, 9999999)}",
            "is_fraud": is_fraud,
            "typology": typology,
            "case_id": case_id,
        }
        self.transactions.append(txn)
        self.next_txn_id += 1
        return txn

    def generate_round_trip_layering(self) -> List[Dict]:
        """
        Round-trip layering: A -> B,C,D (split) -> E (consolidate) -> A (return).
        Total amount: 20L to 1Cr, all within 6-12 hours.
        """
        case_id = f"CASE-{len(self.transactions)//100:05d}"
        origin = random.choice(self.account_pool)
        intermediate_1 = random.sample([a for a in self.account_pool if a != origin], 3)
        hub = random.choice([a for a in self.account_pool if a not in intermediate_1 and a != origin])

        total_amount = random.uniform(2000000, 10000000)  # 20L to 1Cr
        start_time = self.base_date + timedelta(days=random.randint(0, 29))

        # Phase 1: Origin splits to intermediaries
        for i, intermediate in enumerate(intermediate_1):
            split_amount = total_amount / len(intermediate_1) * random.uniform(0.95, 1.05)
            txn_time = start_time + timedelta(minutes=random.randint(2, 15))
            self._add_transaction(
                origin,
                intermediate,
                split_amount,
                txn_time,
                random.choice(["NEFT", "UPI", "IMPS"]),
                is_fraud=True,
                typology="round_trip_layering",
                case_id=case_id,
            )

        # Phase 2: Intermediaries consolidate to hub
        for i, intermediate in enumerate(intermediate_1):
            hub_time = start_time + timedelta(minutes=random.randint(40, 90))
            split_amount = total_amount / len(intermediate_1) * random.uniform(0.93, 0.98)
            self._add_transaction(
                intermediate,
                hub,
                split_amount,
                hub_time,
                random.choice(["NEFT", "IMPS"]),
                is_fraud=True,
                typology="round_trip_layering",
                case_id=case_id,
            )

        # Phase 3: Hub returns to origin (via another intermediary)
        return_time = start_time + timedelta(hours=random.randint(6, 12))
        return_amount = total_amount * random.uniform(0.85, 0.95)
        self._add_transaction(
            hub,
            origin,
            return_amount,
            return_time,
            random.choice(["NEFT", "IMPS"]),
            is_fraud=True,
            typology="round_trip_layering",
            case_id=case_id,
        )

    def generate_structuring(self) -> List[Dict]:
        """
        Structuring: Single source makes 8-15 transfers to different accounts,
        each transfer between 1.5L and 1.9L (just below 2L threshold),
        all within 72 hours.
        """
        case_id = f"CASE-{len(self.transactions)//100:05d}"
        source = random.choice(self.account_pool)
        num_transfers = random.randint(8, 15)
        counterparties = random.sample(
            [a for a in self.account_pool if a != source], num_transfers
        )

        start_time = self.base_date + timedelta(days=random.randint(0, 29))

        for i, counterparty in enumerate(counterparties):
            amount = random.uniform(150000, 190000)  # 1.5L to 1.9L
            txn_time = start_time + timedelta(hours=random.randint(0, 72))
            self._add_transaction(
                source,
                counterparty,
                amount,
                txn_time,
                random.choice(["NEFT", "UPI", "IMPS", "RTGS"]),
                is_fraud=True,
                typology="structuring",
                case_id=case_id,
            )

    def generate_dormant_activation(self) -> List[Dict]:
        """
        Dormant account activation: Account inactive 180+ days receives large inward,
        then sends full amount out within 48 hours.
        """
        case_id = f"CASE-{len(self.transactions)//100:05d}"
        dormant_account = random.choice(self.account_pool)
        inbound_source = random.choice([a for a in self.account_pool if a != dormant_account])
        outbound_dest = random.choice(
            [a for a in self.account_pool if a not in [dormant_account, inbound_source]]
        )

        # Inbound transfer (large amount)
        inbound_time = self.base_date + timedelta(days=random.randint(0, 29))
        amount = random.uniform(500000, 2000000)  # 5L to 20L
        self._add_transaction(
            inbound_source,
            dormant_account,
            amount,
            inbound_time,
            random.choice(["NEFT", "RTGS"]),
            is_fraud=True,
            typology="dormant_activation",
            case_id=case_id,
        )

        # Outbound transfer (within 48 hours)
        outbound_time = inbound_time + timedelta(hours=random.randint(1, 48))
        outbound_amount = amount * random.uniform(0.98, 1.0)
        self._add_transaction(
            dormant_account,
            outbound_dest,
            outbound_amount,
            outbound_time,
            random.choice(["NEFT", "UPI"]),
            is_fraud=True,
            typology="dormant_activation",
            case_id=case_id,
        )

    def generate_fan_out_fan_in(self) -> List[Dict]:
        """
        Fan-out fan-in: Single source -> N intermediaries -> single destination,
        N >= 4, all transfers within 24 hours.
        """
        case_id = f"CASE-{len(self.transactions)//100:05d}"
        source = random.choice(self.account_pool)
        num_intermediaries = random.randint(5, 10)
        intermediaries = random.sample(
            [a for a in self.account_pool if a != source], num_intermediaries
        )
        destination = random.choice(
            [a for a in self.account_pool if a not in [source] + intermediaries]
        )

        total_amount = random.uniform(5000000, 15000000)  # 50L to 1.5Cr
        start_time = self.base_date + timedelta(days=random.randint(0, 29))

        # Fan-out phase
        for intermediate in intermediaries:
            fan_amount = total_amount / num_intermediaries * random.uniform(0.95, 1.05)
            fan_time = start_time + timedelta(minutes=random.randint(0, 120))
            self._add_transaction(
                source,
                intermediate,
                fan_amount,
                fan_time,
                random.choice(["NEFT", "IMPS", "UPI"]),
                is_fraud=True,
                typology="fan_out_fan_in",
                case_id=case_id,
            )

        # Fan-in phase
        for intermediate in intermediaries:
            fan_amount = total_amount / num_intermediaries * random.uniform(0.93, 0.98)
            fan_time = start_time + timedelta(hours=random.randint(2, 24))
            self._add_transaction(
                intermediate,
                destination,
                fan_amount,
                fan_time,
                random.choice(["NEFT", "IMPS"]),
                is_fraud=True,
                typology="fan_out_fan_in",
                case_id=case_id,
            )

    def generate_mule_chain(self) -> List[Dict]:
        """
        Mule chain: Sequential transfers A -> B -> C -> D -> E,
        each transfer 95-100% of previous (slight skimming),
        completed within 12 hours.
        """
        case_id = f"CASE-{len(self.transactions)//100:05d}"
        num_hops = random.randint(4, 6)
        chain = random.sample(self.account_pool, num_hops)

        initial_amount = random.uniform(2000000, 5000000)  # 20L to 50L
        start_time = self.base_date + timedelta(days=random.randint(0, 29))

        current_amount = initial_amount
        for i in range(len(chain) - 1):
            txn_time = start_time + timedelta(hours=random.uniform(0, 12))
            skim_percentage = random.uniform(0.95, 1.0)
            transfer_amount = current_amount * skim_percentage
            self._add_transaction(
                chain[i],
                chain[i + 1],
                transfer_amount,
                txn_time,
                random.choice(["NEFT", "UPI", "IMPS"]),
                is_fraud=True,
                typology="mule_chain",
                case_id=case_id,
            )
            current_amount = transfer_amount

    def generate_clean_transactions(self, count: int) -> None:
        """Generate clean (non-fraudulent) transactions."""
        for _ in range(count):
            sender = random.choice(self.account_pool)
            receiver = random.choice([a for a in self.account_pool if a != sender])
            amount = np.random.lognormal(10.5, 1.5)  # Log-normal distribution
            timestamp = self.base_date + timedelta(
                days=random.randint(0, 29), hours=random.randint(0, 23)
            )
            channel = random.choices(
                ["NEFT", "UPI", "IMPS", "RTGS", "Card"],
                weights=[40, 30, 15, 10, 5],
            )[0]

            self._add_transaction(
                sender,
                receiver,
                amount,
                timestamp,
                channel,
                is_fraud=False,
                typology=None,
                case_id=None,
            )

    def generate_all(self, total_transactions: int = 10000) -> pd.DataFrame:
        """
        Generate all transactions: 90% clean, 10% fraud.
        """
        fraud_count = int(total_transactions * 0.10)
        clean_count = total_transactions - fraud_count

        # Generate fraud scenarios
        fraud_per_typology = fraud_count // 5
        for _ in range(fraud_per_typology):
            self.generate_round_trip_layering()
        for _ in range(fraud_per_typology):
            self.generate_structuring()
        for _ in range(fraud_per_typology):
            self.generate_dormant_activation()
        for _ in range(fraud_per_typology):
            self.generate_fan_out_fan_in()
        for _ in range(fraud_per_typology):
            self.generate_mule_chain()

        # Generate clean transactions
        self.generate_clean_transactions(clean_count)

        # Convert to DataFrame
        df = pd.DataFrame(self.transactions)

        # Shuffle
        df = df.sample(frac=1).reset_index(drop=True)

        return df


def generate_transactions(total_count=10000):
    """Main function to generate synthetic fraud data."""
    print(f"Generating {total_count} synthetic transactions...")
    generator = FraudScenarioGenerator()
    df = generator.generate_all(total_count)

    print(f"✓ Generated {len(df)} transactions")
    print(f"  - Clean: {len(df[df['is_fraud'] == False])} ({len(df[df['is_fraud'] == False])/len(df)*100:.1f}%)")
    print(f"  - Fraud: {len(df[df['is_fraud'] == True])} ({len(df[df['is_fraud'] == True])/len(df)*100:.1f}%)")
    print(f"\nFraud typologies:")
    for typology in df[df['is_fraud'] == True]['typology'].unique():
        count = len(df[df['typology'] == typology])
        print(f"  - {typology}: {count}")

    return df
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
