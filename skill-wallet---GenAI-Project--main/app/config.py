# File: app/config.py
# Part of EduGenie SmartBridge Project

import logging
import os
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("edugenie")

_DEFAULT_SECRET = "your-super-secret-jwt-key-change-this-in-production"

class Settings(BaseSettings):
    # Security Configuration
    SECRET_KEY: str = _DEFAULT_SECRET
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./edugenie.db"

    # AI APIs Configuration
    GEMINI_API_KEY: Optional[str] = None
    HF_API_KEY: Optional[str] = None
    LAMINI_MODEL_URL: str = "https://api-inference.huggingface.co/models/MBZUAI/LaMini-Flan-T5-783M"

    # App Mode
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def warn_insecure_defaults(self) -> "Settings":
        """Emit a CRITICAL warning if the default placeholder SECRET_KEY is still in use."""
        if self.GEMINI_API_KEY:
            self.GEMINI_API_KEY = self.GEMINI_API_KEY.strip()
        if self.HF_API_KEY:
            self.HF_API_KEY = self.HF_API_KEY.strip()
            
        if self.SECRET_KEY == _DEFAULT_SECRET:
            logger.critical(
                "SECURITY WARNING: SECRET_KEY is set to the default placeholder value. "
                "All JWTs signed with this key are INSECURE. "
                "Set a strong random SECRET_KEY in your .env file before deploying."
            )
        return self

# Instantiate settings
settings = Settings()
