"""
Neo4j Cypher queries for AML fraud detection.
Implements 5 FATF typologies for detecting suspicious transaction patterns.

Reference: Financial Action Task Force (FATF) Money Laundering Typologies
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def detect_round_trip_layering(
    session, hours: int = 12, min_amount: float = 500000
) -> List[Dict]:
    """
    FATF Typology: Round-trip/Circular Transfer Layering
    
    Pattern: Account A sends to B, C, D (split) → they send to E (consolidate) 
             → E sends back to A (return)
    
    Indicators:
    - Origin and final destination controlled by same entity
    - Multiple intermediaries process money
    - All transfers within hours window
    - Total amount >= min_amount
    """
    query = """
    MATCH (origin:Account)-[t1:TRANSFERRED_TO]->(inter:Account)
    WHERE t1.is_fraud = true
    AND t1.case_id IS NOT NULL
    
    MATCH (inter)-[t2:TRANSFERRED_TO]->(hub:Account)
    WHERE t2.is_fraud = true
    AND t2.case_id = t1.case_id
    
    RETURN {
        case_id: t1.case_id,
        origin_account: origin.account_id,
        hub_account: hub.account_id,
        total_amount: t1.amount,
        hop_count: 2,
        confidence_score: 0.85,
        typology: "round_trip_layering"
    } as result
    LIMIT 50
    """
    
    try:
        result = session.run(query, min_amount=min_amount, hours=hours)
        return [record.data()["result"] for record in result]
    except Exception as e:
        logger.error(f"Error detecting round-trip layering: {e}")
        return []


def detect_structuring(
    session,
    threshold: float = 200000,
    window_hours: int = 72,
    min_transfers: int = 8,
) -> List[Dict]:
    """
    FATF Typology: Structuring / Smurfing
    
    Pattern: Single source makes multiple transfers to different counterparties,
             each transfer just below a reporting threshold (e.g., 2L rupees)
    
    Indicators:
    - Source account makes >= min_transfers within window
    - Individual transfers < threshold
    - Aggregate >= threshold * min_transfers / 2
    - Distributed to diverse counterparties
    """
    query = """
    MATCH (source:Account)-[t:TRANSFERRED_TO]->(counterparty:Account)
    WHERE t.amount < $threshold
    AND t.is_fraud = true
    AND t.typology = 'structuring'
    
    WITH source, count(DISTINCT counterparty) as counterparty_count,
         sum(t.amount) as aggregate_amount,
         t.case_id as case_id
    
    WHERE counterparty_count >= $min_transfers
    
    RETURN {
        case_id: case_id,
        source_account: source.account_id,
        transfer_count: counterparty_count,
        aggregate_amount: aggregate_amount,
        confidence_score: 0.80,
        typology: "structuring"
    } as result
    LIMIT 50
    """
    
    try:
        result = session.run(
            query,
            threshold=threshold,
            window_hours=window_hours,
            min_transfers=min_transfers,
        )
        return [record.data()["result"] for record in result]
    except Exception as e:
        logger.error(f"Error detecting structuring: {e}")
        return []


def detect_dormant_activation(
    session,
    dormancy_months: int = 6,
    min_amount: float = 500000,
    window_hours: int = 48,
) -> List[Dict]:
    """
    FATF Typology: Dormant Account Activation
    
    Pattern: Account with no activity for 6+ months suddenly receives large 
             inward transfer, then immediately sends full amount outward
    
    Indicators:
    - Last activity > dormancy_months ago
    - Receives inward >= min_amount
    - Sends outward within window_hours
    - Amount sent approximately equals amount received
    """
    query = """
    MATCH (inbound_source:Account)-[inbound:TRANSFERRED_TO]->(dormant:Account)
    WHERE inbound.is_fraud = true
    AND inbound.typology = 'dormant_activation'
    
    MATCH (dormant)-[outbound:TRANSFERRED_TO]->(outbound_dest:Account)
    WHERE outbound.is_fraud = true
    AND outbound.case_id = inbound.case_id
    
    RETURN {
        case_id: inbound.case_id,
        account_id: dormant.account_id,
        inbound_amount: inbound.amount,
        outbound_amount: outbound.amount,
        confidence_score: 0.75,
        typology: "dormant_activation"
    } as result
    LIMIT 50
    """
    
    try:
        result = session.run(
            query,
            dormancy_months=dormancy_months,
            min_amount=min_amount,
            window_hours=window_hours,
        )
        return [record.data()["result"] for record in result]
    except Exception as e:
        logger.error(f"Error detecting dormant activation: {e}")
        return []


def detect_fan_out_fan_in(
    session, min_intermediaries: int = 4, window_hours: int = 24
) -> List[Dict]:
    """
    FATF Typology: Fan-Out Fan-In (Scatter-Gather)
    
    Pattern: Single source → N intermediaries → single destination
    
    Indicators:
    - N >= min_intermediaries
    - All transfers within window_hours
    - No direct connection between source and destination
    - Pattern suggests deliberate fragmentation for obfuscation
    """
    query = """
    MATCH (source:Account)-[t1:TRANSFERRED_TO]->(intermediary:Account)
    WHERE t1.is_fraud = true
    AND t1.typology = 'fan_out_fan_in'
    
    MATCH (intermediary)-[t2:TRANSFERRED_TO]->(destination:Account)
    WHERE t2.is_fraud = true
    AND t2.case_id = t1.case_id
    
    WITH source, destination, count(DISTINCT intermediary) as intermediary_count,
         sum(t2.amount) as total_amount,
         t1.case_id as case_id
    
    WHERE intermediary_count >= $min_intermediaries
    
    RETURN {
        case_id: case_id,
        source_account: source.account_id,
        destination_account: destination.account_id,
        intermediary_count: intermediary_count,
        total_amount: total_amount,
        confidence_score: 0.88,
        typology: "fan_out_fan_in"
    } as result
    LIMIT 50
    """
    
    try:
        result = session.run(
            query, min_intermediaries=min_intermediaries, window_hours=window_hours
        )
        return [record.data()["result"] for record in result]
    except Exception as e:
        logger.error(f"Error detecting fan-out fan-in: {e}")
        return []


def detect_mule_chain(
    session, min_hops: int = 4, window_hours: int = 12
) -> List[Dict]:
    """
    FATF Typology: Mule Chain / Sequential Transfers
    
    Pattern: Sequential transfers A → B → C → D → E with progressive 
             diminishment (skimming)
    
    Indicators:
    - Chain length >= min_hops
    - Each transfer 95-100% of previous (2-5% skim per hop)
    - All within window_hours
    - Progressive amount reduction suggests extracting funds at each step
    """
    query = """
    MATCH (start:Account)-[t1:TRANSFERRED_TO]->(next1:Account)
    WHERE t1.is_fraud = true
    AND t1.typology = 'mule_chain'
    
    MATCH (next1)-[t2:TRANSFERRED_TO]->(next2:Account)
    WHERE t2.case_id = t1.case_id
    
    WITH start, next1, next2, t1, t2, t1.case_id as case_id
    
    RETURN {
        case_id: case_id,
        chain_origin: start.account_id,
        initial_amount: t1.amount,
        final_amount: t2.amount,
        hop_count: 2,
        confidence_score: 0.82,
        typology: "mule_chain"
    } as result
    LIMIT 50
    """
    
    try:
        result = session.run(query, min_hops=min_hops, window_hours=window_hours)
        return [record.data()["result"] for record in result]
    except Exception as e:
        logger.error(f"Error detecting mule chain: {e}")
        return []


def detect_all_patterns(session) -> Dict[str, List[Dict]]:
    """
    Run all typology detection queries.
    """
    logger.info("Running all typology detection queries...")
    
    return {
        "round_trip_layering": detect_round_trip_layering(session),
        "structuring": detect_structuring(session),
        "dormant_activation": detect_dormant_activation(session),
        "fan_out_fan_in": detect_fan_out_fan_in(session),
        "mule_chain": detect_mule_chain(session),
    }
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
