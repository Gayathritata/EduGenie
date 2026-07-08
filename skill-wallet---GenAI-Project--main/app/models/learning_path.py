# File: app/models/learning_path.py
# Part of EduGenie SmartBridge Project

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    difficulty = Column(String(50), nullable=False)  # "Beginner", "Intermediate", "Advanced"
    roadmap_data = Column(JSON, nullable=False)  # Roadmap steps and milestones structure
    current_step = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=func.now(), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="learning_paths")

    def __repr__(self) -> str:
        return f"<LearningPath id={self.id} topic={self.topic!r} difficulty={self.difficulty!r} user_id={self.user_id}>"
