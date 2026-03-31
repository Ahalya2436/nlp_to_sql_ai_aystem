from sqlalchemy import Column, Integer, String, ForeignKey,DateTime
from database import Base
from datetime import datetime

class QueryHistory(Base):
    __tablename__ = "query_history"
    __table_args__ = {"schema": "ai_system_db"}   #  Force system DB

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query_text = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

