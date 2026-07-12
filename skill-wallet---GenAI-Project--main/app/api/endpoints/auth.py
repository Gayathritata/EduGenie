# File: app/api/endpoints/auth.py
# Part of EduGenie SmartBridge Project

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.schemas.auth import UserRegister, UserLogin, UserOut, Token
from app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter()

@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """Register a new student."""
    # Check if username exists
    user_exists = db.query(User).filter(User.username == user_in.username).first()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered."
        )
    # Check if email exists
    email_exists = db.query(User).filter(User.email == user_in.email).first()
    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )
        
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/auth/login", response_model=Token)
def login(
    request: Request,
    response: Response,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate student, issue JWT access token, and set HttpOnly session cookie."""
    # Retrieve user by username or email in a case-insensitive way
    login_value = login_data.username.strip().lower()
    user = db.query(User).filter(
        func.lower(User.username) == login_value
    ).first()
    if not user:
        user = db.query(User).filter(
            func.lower(User.email) == login_value
        ).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        # Audit failed attempt
        fail_log = ActivityLog(
            user_id=user.id if user else None,
            action="login_failed",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:255]
        )
        db.add(fail_log)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user.username, "id": user.id})
    
    # Set JWT in HttpOnly Cookie for secure Jinja2 browser views compatibility
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1440 * 60,  # 24 hours
        samesite="lax",
        secure=False,  # Set True in production over HTTPS
        path="/"
    )
    
    # Audit log
    activity = ActivityLog(
        user_id=user.id,
        action="login_success",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:255]
    )
    db.add(activity)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Logs out current user by clearing access token cookie."""
    try:
        # Manually extract token from cookie so we can pass all 3 required
        # positional args to get_current_user(request, db, token).
        # Calling with only (request, db) raises TypeError at runtime.
        cookie_raw = request.cookies.get("access_token", "")
        if cookie_raw.startswith("Bearer "):
            token_value = cookie_raw.split(" ", 1)[1]
        else:
            token_value = cookie_raw or None

        user = get_current_user(request, db, token_value)
        activity = ActivityLog(
            user_id=user.id,
            action="logout",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:255]
        )
        db.add(activity)
        db.commit()
    except Exception:
        # Swallow auth errors — always clear the cookie regardless
        pass

    response.delete_cookie("access_token", path="/")
    return {"status": "success", "message": "Successfully logged out"}

@router.get("/profile", response_model=UserOut)
def read_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile details of currently authenticated student."""
    return current_user
