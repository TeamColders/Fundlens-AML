import math
import hashlib

def extract_node_features(account_data: dict, history: dict = None) -> dict:
    """
    Extracts the 12 features required by the GAT model for an account.
    """
    # Defaults
    history = history or {}
    
    # Example logic mapping raw data to features
    # In a real system, these would be aggregated via Flink or DB queries.
    
    age_days = account_data.get("age_days", 365)
    age_norm = min(age_days / 3650.0, 1.0) # Cap at 10 years
    
    account_type = account_data.get("account_type", "savings")
    type_map = {"savings": 0.0, "current": 1.0, "nri": 2.0}
    type_encoded = type_map.get(account_type.lower(), 0.0)

    avg_amt = history.get("historical_avg_amount", 1000)
    avg_amt_log = math.log(max(avg_amt, 1.0))
    
    return {
        "account_age_normalised": age_norm,
        "kyc_tier": float(account_data.get("kyc_tier", 1)),
        "historical_avg_amount_log": avg_amt_log,
        "velocity_24h": float(history.get("velocity_24h", 0.0)),
        "velocity_7d": float(history.get("velocity_7d", 0.0)),
        "counterparty_entropy": float(history.get("counterparty_entropy", 0.0)),
        "inbound_ratio": float(history.get("inbound_ratio", 0.5)),
        "deviation_from_baseline": float(history.get("deviation_from_baseline", 0.0)),
        "is_dormant": float(account_data.get("is_dormant", False)),
        "kyc_update_pending": float(account_data.get("kyc_update_pending", False)),
        "pep_adjacent": float(account_data.get("is_pep_adjacent", False)),
        "account_type_encoded": type_encoded
    }

def extract_edge_features(transaction_data: dict, history: dict = None) -> dict:
    """
    Extracts the 6 features required by the GAT model for an edge (transaction).
    """
    history = history or {}
    
    amt = transaction_data.get("amount", 0)
    amt_log = math.log(max(amt, 1.0))
    amt_log_norm = min(amt_log / 20.0, 1.0) # Normalise using a rough max log limit
    
    # amount_ratio = amt / sender_historical_avg (passed via history)
    avg_amt = history.get("sender_historical_avg", amt)
    amount_ratio = min((amt / avg_amt) if avg_amt > 0 else 1.0, 10.0)
    
    channel = transaction_data.get("channel", "NEFT")
    channel_map = {"NEFT": 0.0, "IMPS": 1.0, "UPI": 2.0, "RTGS": 3.0, "SWIFT": 4.0}
    
    return {
        "amount_ratio": float(amount_ratio),
        "time_since_last_txn_normalised": float(history.get("time_since_last_txn_norm", 1.0)),
        "channel_encoded": channel_map.get(channel.upper(), 0.0),
        "is_new_counterparty": float(history.get("is_new_counterparty", 1.0)),
        "amount_log_normalised": amt_log_norm,
        "same_branch": float(transaction_data.get("same_branch", 0.0))
    }
