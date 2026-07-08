# File: app/main.py
# Part of EduGenie SmartBridge Project

import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager — the recommended pattern for startup/shutdown logic.
    Replaces module-level side effects which break test isolation and import-time execution.
    """
    # ── STARTUP ──────────────────────────────────────────────────────────────
    try:
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)

    yield  # Application runs here

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("EduGenie application shutting down.")


# Initialize FastAPI App using the lifespan context manager
app = FastAPI(
    title="EduGenie – Google Gemini Powered Learning Assistant",
    description="Production-ready FastAPI backend for EduGenie assistant.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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

# Global HTTPException handler — serves branded 404 HTML page for browser requests,
# returns clean JSON for API clients (identified by Accept header).
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")
    if exc.status_code == 404 and "text/html" in accept:
        try:
            _templates = Jinja2Templates(directory="app/templates")
            return _templates.TemplateResponse(
                request, "errors/404.html", status_code=404
            )
        except Exception:
            pass  # Fall through to JSON response if template fails
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

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
    gemini_ready = (
        settings.GEMINI_API_KEY is not None
        and settings.GEMINI_API_KEY not in ("your-gemini-api-key-here", "YOUR_GOOGLE_API_KEY")
    )
    hf_ready = (
        settings.HF_API_KEY is not None
        and settings.HF_API_KEY not in ("your-huggingface-api-key-here", "YOUR_HUGGINGFACE_TOKEN")
    )
    return {
        "status": "healthy",
        "app": "EduGenie Backend Service",
        "version": "1.0.0",
        "database": "connected",
        "gemini_api_configured": gemini_ready,
        "lamini_api_configured": hf_ready,
    }
