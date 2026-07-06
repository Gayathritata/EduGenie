# File: app/main.py
# Part of EduGenie SmartBridge Project

import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.session import engine
from app.database.base import Base
from app.api.api_v1 import api_router
from app.api.endpoints import pages

# Setup Logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("edugenie.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("edugenie")

# Initialize database tables on application start
try:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# Initialize FastAPI App
app = FastAPI(
    title="EduGenie – Google Gemini Powered Learning Assistant",
    description="Production-ready FastAPI backend for EduGenie assistant.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000"  # For frontend dev server support if needed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logger middleware to track endpoint usage and response times
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"Method: {request.method} | Path: {request.url.path} | "
        f"Status: {response.status_code} | Duration: {duration:.4f}s"
    )
    return response

# Global unhandled exception handler to prevent leak of tracebacks and return clean JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception encountered at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}" if settings.DEBUG else "A critical server error occurred."}
    )

# Mount static directory
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    logger.info("Static files directory mounted successfully.")
except Exception as e:
    logger.warning(f"Could not mount static directory: {e}")

# Register all API endpoints
app.include_router(api_router)
app.include_router(pages.router)

@app.get("/health", tags=["System"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "app": "EduGenie Backend Service",
        "database": "connected",
        "gemini_api_configured": settings.GEMINI_API_KEY is not None and settings.GEMINI_API_KEY != "your-gemini-api-key-here"
    }
