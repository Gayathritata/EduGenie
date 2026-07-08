# File: app/models/saved_response.py
# Part of EduGenie SmartBridge Project

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class SavedResponse(Base):
    __tablename__ = "saved_responses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_response_id = Column(Integer, ForeignKey("responses.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # "qa", "explain", "roadmap", "quiz", "summary"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="saved_responses")
    source_response = relationship("AIResponse", back_populates="saved_instances")

    def __repr__(self) -> str:
        return f"<SavedResponse id={self.id} category={self.category!r} user_id={self.user_id}>"
