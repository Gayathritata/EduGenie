# File: app/schemas/history.py
# Part of EduGenie SmartBridge Project

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class HistoryOut(BaseModel):
    id: int
    action: str
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None
    description: str
    created_at: datetime

    class Config:
        from_attributes = True

class SavedRequest(BaseModel):
    source_response_id: Optional[int] = Field(None, description="Optional ID of the source AIResponse that generated this content")
    title: str = Field(..., min_length=1, max_length=255, description="Custom bookmark title")
    category: str = Field(..., pattern="^(qa|explain|roadmap|quiz|summary)$", description="Target response category")
    content: str = Field(..., min_length=1, description="Bookmarks text or payload details")

class SavedResponseOut(BaseModel):
    id: int
    source_response_id: Optional[int]
    title: str
    category: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
