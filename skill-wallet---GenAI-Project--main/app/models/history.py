# File: app/models/history.py
# Part of EduGenie SmartBridge Project

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., "asked_question", "completed_quiz"
    entity_id = Column(Integer, nullable=True)  # Reference ID of the target resource
    entity_type = Column(String(50), nullable=True)  # Type of target resource: e.g., "quiz", "learning_path"
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="history_logs")
