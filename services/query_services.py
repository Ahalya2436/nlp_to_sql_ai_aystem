import time
from datetime import datetime, timezone
from fastapi import HTTPException

from services.vllm_service import ask_llm
from services.schema_services import get_schema_description
from services.schema_vector_services import (
    store_schema_embeddings,
    search_schema,
    schema_embeddings_exist
)

from repositories.query_repository import (
    execute_sql,
    store_history,
    store_query_log
)      

# CONFIG
USE_SCHEMA_RAG = True
QUERY_CACHE = {}

# SAFE LLM CALL
def safe_llm_call(prompt, schema):
    try:
        return ask_llm(prompt, schema) 
    except Exception as e:
        print("LLM ERROR:", e)
        return None

# VALIDATION
def validate_query(sql_query: str):
    sql = sql_query.strip().lower()

    if not sql.startswith(("select", "show", "desc")):
        return False, "Only SELECT/SHOW/DESC allowed"

    blocked = ["drop", "delete", "update", "insert", "alter", "truncate", "create"]

    for keyword in blocked:
        if keyword in sql:
            return False, f"Blocked keyword: {keyword}"

    if ";" in sql[:-1]:
        return False, "Multiple SQL statements not allowed"

    return True, None


# RETRY PROMPT
def build_retry_prompt(prompt, sql_query, error, schema):

    error = str(error).lower()

    if "unknown column" in error:
        hint = "Check column names and table aliases."

    elif "syntax" in error:
        hint = "Fix SQL syntax."

    elif "doesn't exist" in error:
        hint = "Use correct table names."

    else:
        hint = "Fix the SQL query based on the error."

    return f"""
Fix this SQL query.

User Question:
{prompt}

Previous SQL:
{sql_query}

Error:
{error}

Hint:
{hint}

Schema:
{schema[:800]}

Return ONLY corrected SQL.
"""

# SCHEMA FILTERING
def filter_schema_by_question(schema_text: str, question: str):

    if not schema_text:
        return schema_text

    question = question.lower()

    STOPWORDS = {
        "show", "get", "find", "list", "give",
        "all", "the", "of", "details", "data"
    }

    keywords = [
        word for word in question.split()
        if word not in STOPWORDS and len(word) > 3
    ]

    tables = schema_text.split("\n\n")

    matched_tables = []

    for table_block in tables:

        lines = table_block.lower().split("\n")

        table_name = lines[0].replace("table:", "").strip()

        # STRONG MATCH: table name priority
        if any(keyword in table_name for keyword in keywords):
            matched_tables.append(table_block)
            continue

        # COLUMN MATCH
        if any(keyword in table_block.lower() for keyword in keywords):
            matched_tables.append(table_block)

    # REMOVE DUPLICATES
    matched_tables = list(dict.fromkeys(matched_tables))

    # LIMIT
    matched_tables = matched_tables[:3]

    if not matched_tables:
        return schema_text

    return "\n\n".join(matched_tables)

#Main fun
def handle_prompt(prompt: str, user_id: int, schema: str, db):

    start_time = time.time()

    retry_count = 0
    first_attempt_success = True
    retry_success = False
    hallucination = False
    error_message = None
    status = "success"

    cache_key = f"{schema}:{prompt}"

    # CACHE
    if cache_key in QUERY_CACHE:
        return QUERY_CACHE[cache_key]

    # SCHEMA LOAD (DYNAMIC)
    schema_info = get_schema_description(db, schema)

    if not schema_info:
        raise HTTPException(
            status_code=404,
            detail=f"Schema '{schema}' not found"
        )

    retrieved_schema = None
    filtered_schema = schema_info

    # RAG SCHEMA RETRIEVAL
    if USE_SCHEMA_RAG:

        if not schema_embeddings_exist(schema):
            store_schema_embeddings(db, schema)

        retrieved_schema = search_schema(prompt, schema, db)

        if not retrieved_schema:
            print(" RAG failed — using full schema")
            retrieved_schema = schema_info

    # NEW: SCHEMA FILTERING
    base_schema = retrieved_schema or schema_info
    filtered_schema = filter_schema_by_question(base_schema, prompt)

    # FIRST PROMPT
    sql_prompt = f"""
Generate a MySQL query.

Question:
{prompt}

Schema:
{filtered_schema[:800]}

Rules:
- Use correct tables and columns
- Use joins if needed
- Return only SQL
"""

    sql_query = safe_llm_call(sql_prompt, filtered_schema)

    # RETRY IF LLM FAILS
    if not sql_query:
        first_attempt_success = False
        retry_count = 1

        retry_prompt = f"""
Generate a simple SQL query for:

{prompt}

Schema:
{filtered_schema[:800]}

Return only SQL.
"""
        sql_query = safe_llm_call(retry_prompt, filtered_schema)

        if not sql_query:
            raise HTTPException(
                status_code=500,
                detail="LLM failed twice"
            )

    # CLEAN SQL
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    # VALIDATION
    valid, err = validate_query(sql_query)

    if not valid:
        raise HTTPException(
            status_code=400,
            detail=err
        )

    # EXECUTION + RETRY
    try:
        result = execute_sql(db, sql_query, schema)
        success = True

    except Exception as e:
        first_attempt_success = False
        retry_count = 1
        error_message = str(e)

        retry_prompt = build_retry_prompt(
            prompt,
            sql_query,
            error_message,
            filtered_schema
        )

        sql_query = safe_llm_call(retry_prompt, filtered_schema)

        if not sql_query:
            raise HTTPException(
                status_code=500,
                detail="Retry failed"
            )

        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        try:
            result = execute_sql(db, sql_query, schema)
            success = True
            retry_success = True

        except Exception as final_error:
            result = {"error": str(final_error)}
            success = False
            hallucination = True
            error_message = str(final_error)
            status = "fail"


    # METRICS
    execution_time = round((time.time() - start_time) * 1000, 2)
    row_count = len(result) if isinstance(result, list) else 0
    slow_query = execution_time > 500

    # STORE LOG
    store_query_log(
        db=db,
        user_id=user_id,
        schema=schema,
        prompt=prompt,
        sql=sql_query,
        exec_time=execution_time,
        success=success,
        rows=row_count,
        created_at=datetime.now(timezone.utc),
        model_name="vllm",
        retry_count=retry_count,
        slow_query=slow_query,
        retrieved_schema=base_schema,
        rag_enabled=USE_SCHEMA_RAG,
        error_message=error_message,
        hallucination=hallucination,
        confidence_score=1.0,
        first_attempt_success=first_attempt_success

    )

    if user_id:
        store_history(db, sql_query)
        # Decide status code
    if success:
        status_code = 200
        status = "success"
    else:
        status_code = 500
        status = "fail"


    # FINAL RESPONSE
    response = {
        "status_code":status_code,
        "status": status,
        "schema": schema,
        "model_used": "vllm_llama3_gpu",
        "sql_query": sql_query,
        "result": result,
        "retrieved_schema": base_schema,
        "filtered_schema": filtered_schema,
        "data":result,  
        "evaluation": {
            "success": success,
            "retry_count": retry_count,
            "retry_success": retry_success,
            "first_attempt_success": first_attempt_success,
            "hallucination": hallucination,
            "execution_time_ms": execution_time
        }
    }

    # CACHE
    QUERY_CACHE[cache_key] = response

    return response