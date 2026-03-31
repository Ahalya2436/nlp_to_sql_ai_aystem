from sqlalchemy import text


# ==============================
# 1. OVERALL MODEL METRICS
# ==============================
def get_model_metrics(db):

    row = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            SUM(success = 1) as success,
            SUM(first_attempt_success = 1) as first_success,
            AVG(execution_time_ms) as avg_time
        FROM ai_system_db.query_logs
    """)).fetchone()

    total, success, first_success, avg_time = row

    total = total or 0
    success = success or 0
    first_success = first_success or 0
    avg_time = avg_time or 0

    final_success_rate = (success / total * 100) if total else 0
    first_attempt_rate = (first_success / total * 100) if total else 0
    retry_improvement = final_success_rate - first_attempt_rate

    return {
        "total_queries": total,
        "final_success_rate_percent": round(final_success_rate, 2),
        "first_attempt_success_rate_percent": round(first_attempt_rate, 2),
        "retry_improvement_percent": round(retry_improvement, 2),
        "avg_execution_time_ms": round(avg_time, 2)
    }


# ==============================
# 2. RETRY ANALYSIS (CORRECTED)
# ==============================
def retry_analysis(db):

    row = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            SUM(retry_count > 0) as retried,
            SUM(retry_count > 0 AND success = 1) as retry_success
        FROM ai_system_db.query_logs
    """)).fetchone()

    total, retried, retry_success = row

    total = total or 0
    retried = retried or 0
    retry_success = retry_success or 0

    retry_rate = (retried / total * 100) if total else 0
    retry_success_rate = (retry_success / retried * 100) if retried else 0

    return {
        "retry_rate_percent": round(retry_rate, 2),
        "retry_success_rate_percent": round(retry_success_rate, 2)
    }


# ==============================
# 3. ACCURACY OVER TIME
# ==============================
def accuracy_per_day(db):

    rows = db.execute(text("""
        SELECT
            DATE(created_at) AS day,
            COUNT(*) AS total,
            SUM(success = 1) AS success_count
        FROM ai_system_db.query_logs
        WHERE created_at IS NOT NULL
        GROUP BY DATE(created_at)
        ORDER BY day DESC;
    """)).fetchall()

    result = []

    for row in rows:
        total = row[1]
        success = row[2]
        accuracy = (success / total * 100) if total else 0

        result.append({
            "date": row[0].isoformat() if row[0] else None,
            "total_queries": total,
            "success": success,
            "accuracy_percent": round(accuracy, 2)
        })

    return result


# ==============================
# 4. FAILING PROMPTS
# ==============================
def failing_prompts(db):

    rows = db.execute(text("""
        SELECT prompt, COUNT(*) AS fail_count
        FROM ai_system_db.query_logs
        WHERE success = 0
        GROUP BY prompt
        ORDER BY fail_count DESC
        LIMIT 10
    """)).fetchall()

    return [
        {"prompt": r[0], "fail_count": r[1]}
        for r in rows
    ]


# ==============================
# 5. ERROR ANALYSIS (NEW 🔥)
# ==============================
def error_analysis(db):

    rows = db.execute(text("""
        SELECT error_message, COUNT(*) as count
        FROM ai_system_db.query_logs
        WHERE success = 0 AND error_message IS NOT NULL
        GROUP BY error_message
        ORDER BY count DESC
        LIMIT 5
    """)).fetchall()

    return [
        {
            "error": r[0],
            "count": r[1]
        }
        for r in rows
    ]


# ==============================
# 6. SLOW QUERY ANALYSIS
# ==============================
def slow_queries(db):

    rows = db.execute(text("""
        SELECT prompt, execution_time_ms
        FROM ai_system_db.query_logs
        WHERE execution_time_ms > (
            SELECT AVG(execution_time_ms) * 1.5 
            FROM ai_system_db.query_logs
        )
        ORDER BY execution_time_ms DESC
        LIMIT 10
    """)).fetchall()

    return [
        {
            "prompt": r[0],
            "execution_time_ms": r[1]
        }
        for r in rows
    ]


# ==============================
# 7. DASHBOARD SUMMARY (🔥 USE THIS API)
# ==============================
def get_dashboard_summary(db):

    return {
        "model_metrics": get_model_metrics(db),
        "retry_analysis": retry_analysis(db),
        "accuracy_trend": accuracy_per_day(db),
        "failing_prompts": failing_prompts(db),
        "error_analysis": error_analysis(db),
        "slow_queries": slow_queries(db)
    }