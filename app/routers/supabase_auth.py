from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from app.api.auth.supabase import get_current_supabase_user, get_optional_supabase_user, cleanup_user_session
from app.schemas.data_models.User import UserRead, SupabaseUserCreate, Token
from app.models.data_models.User import User
from app.models.enums.UserRole import UserRole
from sqlmodel import Session, select
from app.db.database import get_db
from typing import Dict, Any, Optional
from app.api.mvp.auth import create_access_token, create_refresh_token
from app.api.mvp.rules import get_rules_by_organization_id
import uuid
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SUPABASE_USER_PASSWORD_PLACEHOLDER = "SUPABASE_AUTH"

# Helper function to convert string role to UserRole enum
def convert_role_to_enum(role_str: Optional[str]) -> Optional[UserRole]:
    if not role_str:
        return None
        
    try:
        # Normalize to lowercase
        role_str = role_str.lower()
        
        # Match to enum value
        if role_str == "owner":
            return UserRole.OWNER
        elif role_str == "manager":
            return UserRole.MANAGER
        elif role_str == "staff":
            return UserRole.STAFF
        else:
            logger.warning(f"Unknown role value: {role_str}")
            return None
    except (AttributeError, ValueError) as e:
        logger.warning(f"Error converting role {role_str}: {str(e)}")
        return None

router = APIRouter(
    prefix="/supabase-auth",
    tags=["supabase-authentication"]
)

@router.get("/me", response_model=UserRead)
async def get_supabase_user_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get the current authenticated Supabase user's information"""
    try:
        # Get the supabase user from the token
        supabase_user = await get_current_supabase_user(request)
        
        supabase_id = supabase_user.get("id")
        if not supabase_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase user information"
            )
        
        logger.info(f"Getting user info for Supabase ID: {supabase_id}")
        
        # Find or create the user in our database
        user = db.exec(select(User).where(User.supabase_id == supabase_id)).first()
        
        if not user:
            email = supabase_user.get("email")
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is required"
                )
            
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
            logger.info(f"Created new user with ID: {user.id}")
        
        return user
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user information: {str(e)}"
        )

@router.post("/sync", response_model=Token)
async def sync_supabase_user(
    request: Request,
    db: Session = Depends(get_db),
    user_data: Optional[Dict[str, Any]] = None
):
    """
    Synchronize the Supabase user with our database.
    
    The data can come from either:
    1. The Supabase JWT token in the Authorization header (preferred)
    2. The request body with user data (fallback)
    
    Returns a local JWT token that can be used with all endpoints.
    """
    # First try to get data from token
    supabase_user = await get_optional_supabase_user(request)
    
    # If we couldn't get a user from token, try to get it from request body
    if not supabase_user:
        # Try to parse request body if it doesn't match our schema
        if not user_data:
            try:
                body = await request.json()
                user_data = body
            except Exception as e:
                logger.warning(f"Failed to parse request body: {str(e)}")
                user_data = {}
        
        # Now check if we have the minimum required fields
        if user_data and "email" in user_data and "supabase_id" in user_data:
            supabase_id = user_data.get("supabase_id")
            email = user_data.get("email")
            role = user_data.get("role")
            logger.info(f"Using request body data for user {email}, role: {role}")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid user information provided in token or request body"
            )
    else:
        supabase_id = supabase_user.get("id")
        email = supabase_user.get("email")
        # Extract role from user metadata if available
        user_metadata = supabase_user.get("user_metadata", {})
        role = user_metadata.get("role")
        
        logger.info(f"Successfully validated Supabase token for user {email}, role: {role}")
    
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
        
        # Convert role string to UserRole enum if it exists
        role_enum = convert_role_to_enum(role) if role else None
        
        if user:
            logger.info(f"Found existing user by Supabase ID: {user.email}")
            if user.email != email:
                user.email = email
            
            # Update role if it was provided and different from current
            if role_enum and user.role != role_enum:
                old_role = user.role
                user.role = role_enum
                logger.info(f"Updated user role from {old_role} to {role_enum}")
            
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            logger.info(f"No user found with Supabase ID, checking by email: {email}")
            user = db.exec(select(User).where(User.email == email)).first()
            
            if user:
                logger.info(f"Found user by email: {email}, linking to Supabase ID: {supabase_id}")
                user.supabase_id = supabase_id
                
                # Update role if it was provided and different from current
                if role_enum and user.role != role_enum:
                    old_role = user.role
                    user.role = role_enum
                    logger.info(f"Updated user role from {old_role} to {role_enum}")
            else:
                logger.info(f"Creating new user with email: {email} and Supabase ID: {supabase_id}")
                
                # Use provided role or default to STAFF
                user_role = role_enum if role_enum else UserRole.STAFF
                logger.info(f"Setting new user role to: {user_role}")
                
                user = User(
                    email=email,
                    supabase_id=supabase_id,
                    password_hash=SUPABASE_USER_PASSWORD_PLACEHOLDER,
                    id=uuid.uuid4(),
                    role=user_role
                )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Saved user {user.id} to database with role {user.role}")
        
        # Generate JWT tokens using our local JWT system
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    except Exception as e:
        logger.error(f"Error syncing user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@router.post("/logout")
async def logout(
    request: Request
):
    
    if supabase_user:
        supabase_id = supabase_user.get("id")
        logger.info(f"User with Supabase ID {supabase_id} logged out")
        
        await cleanup_user_session(supabase_id)
    else:
        logger.info("Logout requested without valid session")
    
    return {"status": "success", "message": "Logged out successfully"}

@router.post("/token", response_model=Token)
async def get_local_token_from_supabase(
    request: Request,
    db: Session = Depends(get_db)
):
    """Exchange Supabase token for a local JWT token"""
    try:
        # Get the Supabase user from the token
        supabase_user = await get_current_supabase_user(request)
        
        if not supabase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token"
            )
        
        supabase_id = supabase_user.get("id")
        if not supabase_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase user information"
            )
        
        # Find or create the user in our database
        user = db.exec(select(User).where(User.supabase_id == supabase_id)).first()
        
        if not user:
            email = supabase_user.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is required"
                )
            
            # Create new user
            user = User(
                email=email,
                supabase_id=supabase_id,
                password_hash=SUPABASE_USER_PASSWORD_PLACEHOLDER,
                id=uuid.uuid4()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create local JWT tokens
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return Token(access_token=access_token, refresh_token=refresh_token)
        
    except Exception as e:
        logger.error(f"Error exchanging token: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

@router.post("/join-organization", response_model=UserRead)
async def join_organization(
    request: Request,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Join an existing organization using an organization code"""
    try:
        # Get the current user from Supabase token
        supabase_user = await get_current_supabase_user(request)
        
        if not supabase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get organization ID from request body
        organization_id = data.get("organization_id")
        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization ID is required"
            )
        
        # Validate organization ID format
        try:
            organization_id = int(organization_id)
            if organization_id < 100000 or organization_id > 999999:
                raise ValueError("Invalid organization ID format")
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization ID must be a 6-digit number"
            )
        
        # Check if organization exists
        rules = get_rules_by_organization_id(db, organization_id)
        
        if not rules:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Find the user in our database
        supabase_id = supabase_user.get("id")
        user = db.exec(select(User).where(User.supabase_id == supabase_id)).first()
        
        if not user:
            # Try to find by email
            email = supabase_user.get("email")
            user = db.exec(select(User).where(User.email == email)).first()
            
            if not user:
                # Create a new user
                user_metadata = supabase_user.get("user_metadata", {})
                role_str = user_metadata.get("role", "staff")
                role = convert_role_to_enum(role_str) or UserRole.STAFF
                
                user = User(
                    email=supabase_user.get("email"),
                    supabase_id=supabase_id,
                    password_hash=SUPABASE_USER_PASSWORD_PLACEHOLDER,
                    role=role,
                    organization_id=organization_id,
                    id=uuid.uuid4()
                )
                db.add(user)
            else:
                # Update existing user with Supabase ID
                user.supabase_id = supabase_id
        
        # Update user's organization ID
        user.organization_id = organization_id
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User {user.email} joined organization {organization_id}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining organization: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error joining organization: {str(e)}"
        )