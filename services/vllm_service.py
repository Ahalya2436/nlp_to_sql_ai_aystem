import requests
from core.config import settings
from sqlalchemy import text

# INTERNAL VLLM CALL
def _call_vllm(messages: list, temperature: float = 0):

    headers = {
        "Authorization": settings.VLLM_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "model": settings.VLLM_MODEL,
        "messages": messages,
        "temperature": temperature
    }

    try:
        response = requests.post(
            settings.VLLM_URL,
            headers=headers,
            json=payload,
            timeout=120   #increased timeout
        )

        # Check API response
        if response.status_code != 200:
            print("LLM ERROR STATUS:", response.status_code)
            print("LLM ERROR BODY:", response.text)
            return None

        result = response.json()

        # Safe parsing
        content = (
            result.get("choices", [{}])[0]
                  .get("message", {})
                  .get("content", "")
        )

        return content.strip()

    except Exception as e:
        print("LLM ERROR:", e)
        return None

# MAIN SQL GENERATION
def ask_llm(user_input: str, schema_info: str):

    prompt = f"""
You are an expert MySQL SQL generator.

Convert natural language into SQL query.

DATABASE SCHEMA:
{schema_info[:800]}

STRICT RULES:
1. Every table in the SQL must appear in the schema.
2. Every column in the SQL must appear in the schema. 
3. Return only SQL 
4. NEVER create new table names and new column names. 
5. NEVER guess business logic. 
6. ONLY generate SELECT queries. 
7. Do not explain anything. 
8.If aggregate functions (COUNT, SUM, MAX, MIN, AVG) are used, always include appropriate GROUP BY columns.

User Question:
{user_input}

SQL:
"""

    messages = [
        {"role": "system", "content": "You generate only SQL queries."},
        {"role": "user", "content": prompt}
    ]

    response = _call_vllm(messages, temperature=0) 

    if not response:
        return None

    # Clean output
    sql = (
        response.replace("```sql", "")
                .replace("```", "")
                .replace("\\n", " ")
                .replace("\n", " ")
                .strip()
    )

    return sql

# KEYWORD SEARCH
def keyword_schema_search(db, database_name, question):

    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :db
    """)

    rows = db.execute(query, {"db": database_name}).fetchall()

    tables = [r[0] for r in rows]

    question = question.lower()

    matched = [
        table for table in tables
        if table.lower() in question
    ]

    return matched

# RELATIONSHIP EXPANSION
def expand_with_relationships(db, database_name, schema_chunks):

    fk_query = text("""
        SELECT table_name, referenced_table_name
        FROM information_schema.key_column_usage
        WHERE table_schema = :db
        AND referenced_table_name IS NOT NULL
    """)

    rows = db.execute(fk_query, {"db": database_name}).fetchall()

    related = set()

    for table, ref_table in rows:
        for chunk in schema_chunks:
            if table in chunk or ref_table in chunk:
                related.add(table)
                related.add(ref_table)

    return list(related)