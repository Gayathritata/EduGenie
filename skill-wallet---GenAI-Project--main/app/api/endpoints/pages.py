# File: app/api/endpoints/pages.py
# Part of EduGenie SmartBridge Project

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse, tags=["Views"])
def get_landing(request: Request, db: Session = Depends(get_db)):
    """Serve the landing page as the default entry point."""
    response = templates.TemplateResponse(request, "landing.html")
    if request.cookies.get("access_token"):
        response.delete_cookie("access_token", path="/")
    return response

@router.get("/login", response_class=HTMLResponse, tags=["Views"])
def get_login(request: Request, db: Session = Depends(get_db)):
    """Serve the login view without forcing the dashboard."""
    response = templates.TemplateResponse(request, "auth/login.html")
    if request.cookies.get("access_token"):
        response.delete_cookie("access_token", path="/")
    return response

@router.get("/register", response_class=HTMLResponse, tags=["Views"])
def get_register(request: Request, db: Session = Depends(get_db)):
    """Serve the registration view without forcing the dashboard."""
    response = templates.TemplateResponse(request, "auth/register.html")
    if request.cookies.get("access_token"):
        response.delete_cookie("access_token", path="/")
    return response

@router.get("/dashboard", response_class=HTMLResponse, tags=["Views"])
def get_dashboard(request: Request, db: Session = Depends(get_db)):
    """Serve the dashboard workspace for both guests and signed-in users."""
    try:
        current_user = get_current_user(request, db)
        return templates.TemplateResponse(request, "dashboard/index.html", {"user": current_user})
    except Exception:
        response = templates.TemplateResponse(request, "dashboard/index.html", {"user": None})
        if request.cookies.get("access_token"):
            response.delete_cookie("access_token", path="/")
        return response
