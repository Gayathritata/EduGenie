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
def get_landing(request: Request):
    """Serve the Landing page view."""
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("landing.html", {"request": request})

@router.get("/login", response_class=HTMLResponse, tags=["Views"])
def get_login(request: Request):
    """Serve the Login view."""
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse, tags=["Views"])
def get_register(request: Request):
    """Serve the Registration view."""
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse, tags=["Views"])
def get_dashboard(request: Request, db: Session = Depends(get_db)):
    """Serve the authenticated Dashboard workspace."""
    try:
        current_user = get_current_user(request, db)
        return templates.TemplateResponse("dashboard/index.html", {"request": request, "user": current_user})
    except Exception:
        # Redirect to login page if user session is invalid
        return RedirectResponse(url="/login?msg=unauthorized")
