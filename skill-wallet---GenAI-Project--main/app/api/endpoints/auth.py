# File: app/api/endpoints/auth.py
# Part of EduGenie SmartBridge Project

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
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
    response: Response,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate student, issue JWT access token, and set HttpOnly session cookie."""
    # Retrieve user by username or email
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
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
        secure=False  # Set True in production over HTTPS
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/logout")
def logout(response: Response):
    """Logs out current user by clearing access token cookie."""
    response.delete_cookie("access_token")
    return {"status": "success", "message": "Successfully logged out"}

@router.get("/profile", response_model=UserOut)
def read_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile details of currently authenticated student."""
    return current_user
