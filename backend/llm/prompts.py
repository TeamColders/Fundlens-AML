"""
FundLens — LLM prompt templates.
All prompts live here so they can be tuned independently of the API logic.
"""
from datetime import date


def build_str_prompt(case_data: dict) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for STR-01 generation.
    case_data keys: case_id, typology_name, typology_fatf_reference,
                    total_amount, accounts_count, hop_count, duration_hours,
                    gnn_score, channel, timeline (list of dicts), subgraph
    """
    today = date.today().strftime("%d %b %Y")

    # Build timeline text
    timeline_text = ""
    if case_data.get("timeline"):
        timeline_text = "\nTRANSACTION TIMELINE:\n"
        for txn in case_data["timeline"]:
            timeline_text += (
                f"  {txn.get('timestamp','')}  "
                f"{txn.get('sender','')} → {txn.get('receiver','')}  "
                f"₹{txn.get('amount',0):,.0f}  "
                f"[{txn.get('channel','')}]\n"
            )

    # Build account roles text
    accounts_text = ""
    if case_data.get("subgraph") and case_data["subgraph"].get("nodes"):
        accounts_text = "\nACCOUNTS INVOLVED:\n"
        for node in case_data["subgraph"]["nodes"]:
            role = "Hub" if node.get("is_hub") else \
                   "Origin" if node.get("is_origin") else \
                   "Dormant-Activated" if node.get("is_dormant") else "Intermediary"
            accounts_text += (
                f"  {node['id']}  Role: {role}  "
                f"Risk: {node.get('risk_level','').upper()}  "
                f"Type: {node.get('account_type','')}\n"
            )

    confidence_pct = round(case_data.get("gnn_score", 0) * 100, 1)
    duration_h = case_data.get("duration_hours", 0)
    duration_str = f"{int(duration_h)}h {int((duration_h % 1)*60)}m"

    system_prompt = """You are a senior Anti-Money Laundering compliance officer at \
Union Bank of India with 15 years of experience filing Suspicious Transaction Reports \
with the Financial Intelligence Unit of India (FIU-IND). You write precise, formal, \
legally accurate STR narratives that are never ambiguous. You always cite specific \
regulatory references. You never speculate — you report observable patterns and facts. \
Your language is formal, measured, and suitable for submission to a government authority \
and potential use as evidence in prosecution proceedings."""

    user_prompt = f"""Generate a complete FIU-IND Form STR-01 for the following case.

CASE DETAILS:
  Case Reference:    {case_data.get("case_id", "CASE-UNKNOWN")}
  Filing Date:       {today}
  Filing Entity:     Union Bank of India
  Typology:          {case_data.get("typology_name", "")}
  FATF Reference:    {case_data.get("typology_fatf_reference", "")}
  GNN Confidence:    {confidence_pct}%
  Total Amount:      ₹{case_data.get("total_amount", 0):,.0f}
  Accounts Involved: {case_data.get("accounts_count", 0)}
  Transaction Hops:  {case_data.get("hop_count", 0)}
  Duration:          {duration_str}
  Channel(s):        {case_data.get("channel", "")}
{accounts_text}{timeline_text}

Output EXACTLY this structure — no additional commentary, no markdown:

FIU-IND FORM STR-01 (DRAFT)
Report Date: {today}
Filing Entity: Union Bank of India

CASE REF: {case_data.get("case_id", "")}
TYPOLOGY: {case_data.get("typology_name", "")}
RISK SCORE: {confidence_pct}% (GNN confidence)
ACCOUNTS INVOLVED: {case_data.get("accounts_count", 0)}
TOTAL AMOUNT: ₹{case_data.get("total_amount", 0):,.0f}
PERIOD: {duration_str}

NARRATIVE:
[Write 3-4 paragraphs. Paragraph 1: what triggered the alert and which account was the \
origin. Paragraph 2: how the funds moved — the specific hop sequence, amounts, channels, \
and timing. Paragraph 3: why this matches the named FATF typology — reference the \
structural indicators, velocity, and any dormancy or PEP flags. \
Paragraph 4: the significance of the pattern and why it warrants investigation.]

RECOMMENDED ACTION:
[Specific actionable recommendation: whether to freeze accounts, escalate to ED, \
request source-of-funds declaration, file a CTR in addition, or refer for enhanced \
due diligence. Be specific — name the accounts to act on.]

REGULATORY BASIS:
PMLA 2002, Section 12 and Section 16 | {case_data.get("typology_fatf_reference", "FATF Typology")} | \
RBI Master Circular DBR.AML.BC.No.10/14.01.001/2015-16

HINDI NARRATIVE:
[Translate the NARRATIVE section above into formal Hindi. Preserve all account IDs \
(ACC-XXXX), case references, amounts (₹), and regulatory citations exactly. \
Only translate explanatory prose.]"""

    return system_prompt, user_prompt


def build_hindi_translation_prompt(english_narrative: str) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for Hindi translation of the narrative.
    Only translates the narrative paragraphs — not headers, account IDs, amounts,
    regulatory references, or case IDs.
    """
    system_prompt = """आप एक वरिष्ठ बैंकिंग अनुपालन अधिकारी हैं जो AML रिपोर्ट का \
अनुवाद करते हैं। आप केवल कथा पैराग्राफ का अनुवाद करते हैं। \
खाता संख्याएं (ACC-XXXX), केस आईडी, राशियां, नियामक संदर्भ, \
और प्रॉपर नाउन का अनुवाद न करें।"""

    user_prompt = f"""Translate the following AML report narrative to formal Hindi. \
Preserve all account IDs (ACC-XXXX format), case references, amounts (₹ figures), \
regulatory citations, and proper nouns exactly as they appear. \
Only translate the explanatory text. Use formal banking Hindi terminology.

ENGLISH NARRATIVE:
{english_narrative}

Output only the Hindi translation — no additional commentary."""

    return system_prompt, user_prompt


def build_cypher_prompt(natural_language_query: str, schema: str) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for NL-to-Cypher conversion.
    """
    system_prompt = """You are a Neo4j Cypher expert working with a banking fraud \
detection knowledge graph. You convert natural language questions into precise, \
safe, read-only Cypher queries. You NEVER generate queries with WRITE operations \
(CREATE, MERGE, SET, DELETE, REMOVE, DROP). You return ONLY the Cypher query — \
no explanation, no markdown, no backticks, no comments."""

    examples = """
EXAMPLES:
NL: Show me all accounts connected to ACC-0041
Cypher: MATCH (a:Account {account_id: 'ACC-0041'})-[r]-(b) RETURN a, r, b LIMIT 50

NL: Which accounts received transfers from dormant accounts this week?
Cypher: MATCH (src:Account {is_dormant: true})-[t:TRANSFERRED_TO]->(dst:Account) WHERE t.timestamp >= datetime() - duration('P7D') RETURN dst.account_id, sum(t.amount) as total, count(t) as transfers ORDER BY total DESC

NL: What is the total amount transferred through account ACC-0089?
Cypher: MATCH (a:Account {account_id: 'ACC-0089'}) OPTIONAL MATCH (a)-[out:TRANSFERRED_TO]->() OPTIONAL MATCH ()-[in:TRANSFERRED_TO]->(a) RETURN a.account_id, sum(out.amount) as outbound, sum(in.amount) as inbound, sum(out.amount) + sum(in.amount) as total

NL: Find all accounts with more than 5 transfers in the last 24 hours
Cypher: MATCH (a:Account)-[t:TRANSFERRED_TO]->() WHERE t.timestamp >= datetime() - duration('PT24H') WITH a, count(t) as txn_count WHERE txn_count > 5 RETURN a.account_id, txn_count ORDER BY txn_count DESC

NL: Which accounts share the same entity as ACC-0041?
Cypher: MATCH (a:Account {account_id: 'ACC-0041'})-[:CONTROLLED_BY]->(e:Entity)<-[:CONTROLLED_BY]-(b:Account) WHERE b.account_id <> 'ACC-0041' RETURN b.account_id, e.entity_id
"""

    user_prompt = f"""GRAPH SCHEMA:
{schema}

{examples}

Convert this question to a Cypher query:
{natural_language_query}"""

    return system_prompt, user_prompt


# Default graph schema used in NL-to-Cypher prompts
def build_nl_query_answer_prompt(query: str, context: dict) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for investigative Q&A over case facts.
  context keys: active_case, entity, sql_results, sql_handler, recent_cases, analytics_snippet
    """
    import json

    system_prompt = """You are FundLens, a senior AML investigation analyst at Union Bank of India.
You answer investigator questions using ONLY the facts in the provided context JSON.
Never invent account IDs, amounts, or case references. If data is missing, say what is missing
and what the investigator should check next. Be concise, formal, and actionable.
Do not use markdown headings or bullet lists unless the user asked for a list."""

    compact = {
        "question": query,
        "active_case": context.get("active_case"),
        "entity": context.get("entity"),
        "sql_handler": context.get("sql_handler"),
        "sql_row_count": context.get("sql_row_count"),
        "sql_results_preview": context.get("sql_results_preview"),
        "neo4j_results_preview": context.get("neo4j_results_preview"),
        "recent_cases": context.get("recent_cases"),
    }

    user_prompt = f"""Investigation context (JSON):
{json.dumps(compact, indent=2, default=str)[:12000]}

The investigator asked:
{query}

Respond in EXACTLY this format (no markdown fences):

SUMMARY:
[1-3 sentences: direct answer with specific ACC-/CASE- IDs and ₹ amounts when present]

NARRATIVE:
[Optional. Use 2-4 short paragraphs only when the question asks why, how, explain, recommend,
or summarize patterns. Otherwise write: N/A]"""

    return system_prompt, user_prompt


DEFAULT_GRAPH_SCHEMA = """
Nodes:
  Account {account_id, account_type, status, kyc_tier, created_date,
           last_active_date, declared_income, home_branch, is_dormant,
           total_inbound, total_outbound, counterparty_count}
  Entity  {entity_id, name_hash, pan_hash, mobile_hash, kyc_tier, is_pep}

Relationships:
  (Account)-[:TRANSFERRED_TO {transaction_id, amount, currency, timestamp,
              channel, branch_code, reference_number, is_fraud,
              typology, case_id}]->(Account)
  (Account)-[:CONTROLLED_BY]->(Entity)
  (Account)-[:RELATED_TO {relation_type}]-(Account)
"""
