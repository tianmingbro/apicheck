from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger
from datetime import datetime
from app.db.base import Base

class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(36), unique=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    api_key_id = Column(Integer, index=True, nullable=False)
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_cents = Column(Integer, nullable=False)
    status_code = Column(Integer, index=True)
    duration_ms = Column(Integer)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)