from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

from services.dashboard_services import (
    get_model_metrics,
    accuracy_per_day,
    failing_prompts,
    retry_analysis,
    slow_queries,
    error_analysis,
    get_dashboard_summary
)

from services.schema_vector_services import search_schema, get_embedding

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ==============================
# 🔥 1. FULL DASHBOARD (MAIN API)
# ==============================
@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    return get_dashboard_summary(db)


# ==============================
# 📊 2. MAIN METRICS
# ==============================
@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    return get_model_metrics(db)


# ==============================
# 📈 3. ACCURACY TREND
# ==============================
@router.get("/accuracy-per-day")
def accuracy_day(db: Session = Depends(get_db)):
    return accuracy_per_day(db)


# ==============================
# ❌ 4. FAILING PROMPTS
# ==============================
@router.get("/failing-prompts")
def failing(db: Session = Depends(get_db)):
    return failing_prompts(db)


# ==============================
# 🔁 5. RETRY ANALYSIS (UPDATED)
# ==============================
@router.get("/retry-analysis")
def retry(db: Session = Depends(get_db)):
    return retry_analysis(db)


# ==============================
# 🐞 6. ERROR ANALYSIS (NEW 🔥)
# ==============================
@router.get("/error-analysis")
def errors(db: Session = Depends(get_db)):
    return error_analysis(db)


# ==============================
# ⚡ 7. SLOW QUERIES
# ==============================
@router.get("/slow-queries")
def slow(db: Session = Depends(get_db)):
    return slow_queries(db)


# ==============================
# 🧠 8. RAG DEBUG (KEEP)
# ==============================
@router.get("/rag/debug")
def rag_debug(question: str, database_name: str):

    embedding = get_embedding(question)
    retrieved_schema = search_schema(question, database_name)

    return {
        "question": question,
        "embedding_dimension": len(embedding),
        "retrieved_schema": retrieved_schema
    }