from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from app.api.auth.supabase import get_current_supabase_user, get_optional_supabase_user, cleanup_user_session
from app.schemas.data_models.User import UserRead, SupabaseUserCreate
from app.models.data_models.User import User
from sqlmodel import Session, select
from app.db.database import get_db
from typing import Dict, Any, Optional
import uuid
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SUPABASE_USER_PASSWORD_PLACEHOLDER = "SUPABASE_AUTH"

router = APIRouter(
    prefix="/supabase-auth",
    tags=["supabase-authentication"]
)

@router.get("/me", response_model=UserRead)
async def get_supabase_user_info(
    supabase_user: Dict[str, Any] = Depends(get_current_supabase_user),
    db: Session = Depends(get_db)
):
    """Get the current authenticated Supabase user's information"""
    
    supabase_id = supabase_user.get("id")
    if not supabase_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase user information"
        )
    
    user = db.exec(select(User).where(User.supabase_id == supabase_id)).first()
    
    if not user:
        email = supabase_user.get("email")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        user = User(
            email=email,
            supabase_id=supabase_id,
            password_hash=SUPABASE_USER_PASSWORD_PLACEHOLDER,
            id=uuid.uuid4()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

@router.post("/sync", response_model=UserRead)
async def sync_supabase_user(
    request: Request,
    user_data: Optional[SupabaseUserCreate] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Synchronize the Supabase user with our database.
    
    The data can come from either:
    1. The Supabase JWT token in the Authorization header (preferred)
    2. The request body with user data (fallback)
    """
    supabase_user = await get_optional_supabase_user(request)
    
    if supabase_user:
        supabase_id = supabase_user.get("id")
        email = supabase_user.get("email")
        
        logger.info(f"Successfully validated Supabase token for user {email}")
    elif user_data:
        supabase_id = user_data.supabase_id
        email = user_data.email
        
        logger.info(f"Using request body data for user {email}")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid user information provided in token or request body"
        )
    
    if not supabase_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supabase ID and email are required"
        )
    
    try:
        logger.info(f"Attempting to find or create user with Supabase ID: {supabase_id}")
        
        query = select(User).where(User.supabase_id == supabase_id)
        logger.info(f"Query: {query}")
        user = db.exec(query).first()
        
        if user:
            logger.info(f"Found existing user by Supabase ID: {user.email}")
            if user.email != email:
                user.email = email
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"Updated user email from {user.email} to {email}")
        else:
            logger.info(f"No user found with Supabase ID, checking by email: {email}")
            user = db.exec(select(User).where(User.email == email)).first()
            
            if user:
                logger.info(f"Found user by email: {email}, linking to Supabase ID: {supabase_id}")
                user.supabase_id = supabase_id
            else:
                logger.info(f"Creating new user with email: {email} and Supabase ID: {supabase_id}")
                user = User(
                    email=email,
                    supabase_id=supabase_id,
                    password_hash=SUPABASE_USER_PASSWORD_PLACEHOLDER,
                    id=uuid.uuid4()
                )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Saved user {user.id} to database")
        
        return user
    except Exception as e:
        logger.error(f"Error syncing user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing user: {str(e)}"
        )

@router.post("/logout")
async def logout(
    supabase_user: Dict[str, Any] = Depends(get_optional_supabase_user)
):
    
    if supabase_user:
        supabase_id = supabase_user.get("id")
        logger.info(f"User with Supabase ID {supabase_id} logged out")
        
        await cleanup_user_session(supabase_id)
    else:
        logger.info("Logout requested without valid session")
    
    return {"status": "success", "message": "Logged out successfully"}