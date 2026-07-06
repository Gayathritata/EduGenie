# File: app/schemas/auth.py
# Part of EduGenie SmartBridge Project

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username must be between 3 and 50 characters")
    email: EmailStr = Field(..., description="A valid email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password must be at least 6 characters")

class UserLogin(BaseModel):
    username: str = Field(..., description="Username or Email to login")
    password: str = Field(..., description="Plaintext password")

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
