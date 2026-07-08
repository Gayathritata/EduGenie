# File: app/models/query.py
# Part of EduGenie SmartBridge Project

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=False, index=True)  # "qa", "explain", "quiz_gen", "summarize", "roadmap_gen"
    created_at = Column(DateTime, default=func.now(), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="queries")
    response = relationship("AIResponse", back_populates="query", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Query id={self.id} type={self.query_type!r} user_id={self.user_id}>"
