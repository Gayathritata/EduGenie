# File: app/models/quiz.py
# Part of EduGenie SmartBridge Project

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    questions_data = Column(JSON, nullable=False)  # Stores questions, choices, answers, and explanations
    score = Column(Integer, nullable=True)  # Populated when submitted
    total_questions = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime, default=func.now(), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="quizzes")

    def __repr__(self) -> str:
        return f"<Quiz id={self.id} topic={self.topic!r} user_id={self.user_id} score={self.score}>"
