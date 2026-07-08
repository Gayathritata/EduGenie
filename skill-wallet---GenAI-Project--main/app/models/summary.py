# File: app/models/summary.py
# Part of EduGenie SmartBridge Project

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_text = Column(Text, nullable=False)
    summary_text = Column(Text, nullable=False)
    length_type = Column(String(50), nullable=False)  # "short", "medium", "long"
    created_at = Column(DateTime, default=func.now(), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="summaries")

    def __repr__(self) -> str:
        return f"<Summary id={self.id} length={self.length_type!r} user_id={self.user_id}>"
