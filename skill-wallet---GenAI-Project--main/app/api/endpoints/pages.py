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
    """Serve the Landing page view."""
    try:
        get_current_user(request, db)
        return RedirectResponse(url="/dashboard")
    except Exception:
        response = templates.TemplateResponse(request, "landing.html")
        if request.cookies.get("access_token"):
            response.delete_cookie("access_token")
        return response

@router.get("/login", response_class=HTMLResponse, tags=["Views"])
def get_login(request: Request, db: Session = Depends(get_db)):
    """Serve the Login view."""
    try:
        get_current_user(request, db)
        return RedirectResponse(url="/dashboard")
    except Exception:
        response = templates.TemplateResponse(request, "auth/login.html")
        if request.cookies.get("access_token"):
            response.delete_cookie("access_token")
        return response

@router.get("/register", response_class=HTMLResponse, tags=["Views"])
def get_register(request: Request, db: Session = Depends(get_db)):
    """Serve the Registration view."""
    try:
        get_current_user(request, db)
        return RedirectResponse(url="/dashboard")
    except Exception:
        response = templates.TemplateResponse(request, "auth/register.html")
        if request.cookies.get("access_token"):
            response.delete_cookie("access_token")
        return response

@router.get("/dashboard", response_class=HTMLResponse, tags=["Views"])
def get_dashboard(request: Request, db: Session = Depends(get_db)):
    """Serve the authenticated Dashboard workspace."""
    try:
        current_user = get_current_user(request, db)
        return templates.TemplateResponse(request, "dashboard/index.html", {"user": current_user})
    except Exception:
        # Redirect to login page if user session is invalid
        response = RedirectResponse(url="/login?msg=unauthorized")
        if request.cookies.get("access_token"):
            response.delete_cookie("access_token")
        return response
