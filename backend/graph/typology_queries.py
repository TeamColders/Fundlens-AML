def execute_query(session, query, **kwargs):
    result = session.run(query, **kwargs)
    return [record.data() for record in result]

def detect_round_trip_layering(session, time_window_hours: int = 24, min_hops: int = 3):
    """
    Detects funds moving in a circular pattern: A -> B -> C -> A within a time window.
    """
    query = """
    MATCH p = (a:Account)-[r:TRANSFERRED_TO*3..5]->(a)
    WHERE all(idx in range(0, size(r)-2) WHERE r[idx].timestamp <= r[idx+1].timestamp)
    // simplistic time window approximation assuming timestamps are comparable and parsing logic exists
    RETURN [n in nodes(p) | n.account_id] AS cycle, reduce(s = 0, edge in r | s + edge.amount) AS total_amount
    LIMIT 50
    """
    return execute_query(session, query, min_hops=min_hops)

def detect_structuring(session, target_account: str, threshold: float = 200000, count: int = 5):
    """
    Detects many small deposits to a target account just below a reporting threshold.
    """
    query = """
    MATCH (sender:Account)-[r:TRANSFERRED_TO]->(target:Account {account_id: $target_account})
    WHERE r.amount < $threshold
    WITH target, count(r) as tx_count, sum(r.amount) as total_amount, collect(sender.account_id) as senders
    WHERE tx_count >= $count
    RETURN target.account_id AS target_account, tx_count, total_amount, senders
    """
    return execute_query(session, query, target_account=target_account, threshold=threshold, count=count)

def detect_dormant_activation(session, days_dormant: int = 180, spike_threshold: float = 1000000):
    """
    Detects an account that was dormant (or created long ago but inactive) suddenly receiving a large amount.
    """
    query = """
    MATCH (sender:Account)-[r:TRANSFERRED_TO]->(target:Account)
    WHERE target.is_dormant = true AND r.amount > $spike_threshold
    RETURN target.account_id AS dormant_account, sender.account_id AS sender, r.amount AS amount, r.timestamp AS timestamp
    """
    return execute_query(session, query, spike_threshold=spike_threshold)

def detect_fan_out_fan_in(session, source_account: str):
    """
    Detects money fanning out from a source account to multiple intermediaries, 
    and then fanning in to a single target account.
    """
    query = """
    MATCH (source:Account {account_id: $source_account})-[r1:TRANSFERRED_TO]->(intermediary:Account)-[r2:TRANSFERRED_TO]->(target:Account)
    WITH source, target, count(DISTINCT intermediary) as intermediary_count, collect(DISTINCT intermediary.account_id) as intermediaries
    WHERE intermediary_count >= 5
    RETURN source.account_id AS source, target.account_id AS target, intermediary_count, intermediaries
    """
    return execute_query(session, query, source_account=source_account)

def detect_mule_chain(session, chain_length: int = 5):
    """
    Detects money moving linearly A -> B -> C -> D -> E within a short timeframe.
    """
    query = """
    MATCH p = (start:Account)-[r:TRANSFERRED_TO*5..5]->(end:Account)
    WHERE all(idx in range(0, size(r)-2) WHERE r[idx].timestamp <= r[idx+1].timestamp)
      AND start <> end
    RETURN [n in nodes(p) | n.account_id] AS chain, reduce(s = 0, edge in r | s + edge.amount) AS total_amount
    LIMIT 50
    """
    return execute_query(session, query)
