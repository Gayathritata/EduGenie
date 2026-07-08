# File: app/models/history.py
# Part of EduGenie SmartBridge Project

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., "asked_question", "completed_quiz"
    entity_id = Column(Integer, nullable=True)   # Generic FK ref (quiz_id, path_id, etc.)
    entity_type = Column(String(50), nullable=True)  # Defines entity table type: "quiz", "learning_path"
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="history_logs")

    def __repr__(self) -> str:
        return f"<History id={self.id} action={self.action!r} user_id={self.user_id}>"
