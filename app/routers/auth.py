from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.database import get_db
from app.schemas.data_models.User import UserCreate, UserRead, Token
from app.models.data_models.User import User
from app.models.enums.UserRole import UserRole
from app.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token, 
    get_owner_user,
    get_current_user
)
from typing import Optional
from uuid import UUID

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account"""
    # Check if email already exists
    existing_user = db.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role
    )
    
    # Add user to database
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with username (email) and password"""
    # Find user by email
    user = db.exec(select(User).where(User.email == form_data.username)).first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh-token", response_model=Token)
async def refresh_token(token: str, db: Session = Depends(get_db)):
    """Get new access token using refresh token"""
    try:
        # Validate refresh token
        current_user = await get_current_user(token=token, db=db)
        
        # Generate new tokens
        access_token = create_access_token(data={"sub": str(current_user.id), "role": current_user.role})
        refresh_token = create_refresh_token(data={"sub": str(current_user.id)})
        
        return Token(access_token=access_token, refresh_token=refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's information"""
    return current_user

@router.post("/users", response_model=UserRead)
async def create_user(
    user_data: UserCreate, 
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Create a new user (OWNER role required)"""
    # Check if email already exists
    existing_user = db.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role
    )
    
    # Add user to database
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user 