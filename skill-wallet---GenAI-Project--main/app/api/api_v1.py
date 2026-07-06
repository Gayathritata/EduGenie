# File: app/api/api_v1.py
# Part of EduGenie SmartBridge Project

from fastapi import APIRouter
from app.api.endpoints import auth, ai_core, history

api_router = APIRouter()

# Include routes directly without a sub-prefix to match requested paths exactly
# i.e., /auth/register, /auth/login, /qa, /explain, /quiz, /summarize, /learn, /history, /profile, /save
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(ai_core.router, tags=["AI Core Features"])
api_router.include_router(history.router, tags=["User History & Saved Responses"])
