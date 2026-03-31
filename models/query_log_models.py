from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from datetime import datetime
from database import Base

class QueryLog(Base):
    __tablename__ = "query_logs"
    __table_args__ = {"schema": "ai_system_db"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    schema_name = Column(String(100))
    prompt = Column(Text)
    generated_sql = Column(Text)
    execution_time_ms = Column(Float)
    success = Column(Boolean)
    rows_returned = Column(Integer)
    created_at = Column(DateTime)
    model_name = Column(String(50))
    retry_count = Column(Integer)
    slow_query = Column(Boolean, default=False)
    retrieved_schema = Column(Text, nullable=True)
    rag_enabled = Column(Boolean, default=True)
    error_message = Column(Text(50))
    hallucination = Column(Boolean, default=False)
    confidence_score = Column(Float, default=1.0)
    first_attempt_success = Column(Boolean, default=True)