# File: app/models/response.py
# Part of EduGenie SmartBridge Project

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class AIResponse(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id", ondelete="SET NULL"), unique=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    response_text = Column(Text, nullable=False)
    model_used = Column(String(50), nullable=False)  # e.g., "gemini-1.5-flash", "lamini-flan-t5"
    latency_ms = Column(Integer, nullable=True)  # response generation latency tracking
    created_at = Column(DateTime, default=func.now(), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="responses")
    query = relationship("Query", back_populates="response")
    saved_instances = relationship("SavedResponse", back_populates="source_response", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<AIResponse id={self.id} model={self.model_used!r} user_id={self.user_id}>"
