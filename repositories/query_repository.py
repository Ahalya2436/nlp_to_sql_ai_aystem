import re
from sqlalchemy import text,func
from models.query_model import QueryHistory
from models.query_log_models import QueryLog

def store_query_log(db, user_id, schema, prompt, sql, exec_time, success, rows,created_at, model_name, retry_count,
                     slow_query, retrieved_schema, rag_enabled,error_message,hallucination,confidence_score,first_attempt_success):
    log = QueryLog(
        user_id=user_id,
        schema_name=schema,
        prompt=prompt,
        generated_sql=sql,
        execution_time_ms=exec_time,
        success=success,
        rows_returned=rows,
        created_at=created_at,
        model_name=model_name,
        retry_count=retry_count,
        slow_query=slow_query,
        retrieved_schema=retrieved_schema,
        rag_enabled=rag_enabled,
        error_message=error_message,
        hallucination=hallucination,
        confidence_score=confidence_score,
        first_attempt_success=first_attempt_success

    )

    db.add(log)
    db.commit()

# Execute SQL (DB Layer Only)
def execute_sql(db, sql_query, schema):

    try:
        # SWITCH DATABASE
        db.execute(text(f"USE {schema}"))

        result = db.execute(text(sql_query))
        rows = result.fetchall()

        return [dict(r._mapping) for r in rows]

    except Exception as e:
        raise Exception(str(e))

# Get Schema Info Dynamically
def get_schema_info(db, schema_name: str):
    """
    Fetch tables and columns dynamically from information_schema
    """
    schema_text = ""

    tables = db.execute(
        text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
        """),
        {"schema": schema_name}
    ).fetchall()

    for table in tables:
        table_name = table[0]

        columns = db.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = :table
            """),
            {"schema": schema_name, "table": table_name}
        ).fetchall()

        column_list = ",".join([col[0] for col in columns])
        schema_text += f"{table_name}({column_list})\n"

    return schema_text

# Store Query History
def store_history(db, sql_query: str):
    history = QueryHistory(
        query_text=sql_query
    )
    db.add(history)
    db.commit()
# Get User History
def get_user_history(db):
    history = db.query(QueryHistory).all()

    return [
        {
            "id": h.id,
            "query": h.query_text,
            "created_at": h.created_at
        }
        for h in history
    ]
