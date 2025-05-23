from datetime import datetime, timedelta
from typing import Optional, Callable
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.db.database import get_db
from app.models.data_models.User import User
from app.models.enums.UserRole import UserRole
from app.api.auth.supabase import get_token_from_header
from app.api.mvp.rules import get_rules_by_organization_id

import os
import logging

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

logger.info(f"JWT Auth Config Loaded: SECRET_KEY is set: {bool(SECRET_KEY)}, ALGORITHM: {ALGORITHM}, EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")
if not SECRET_KEY:
    logger.error("CRITICAL: JWT_SECRET environment variable is NOT SET.")
if not ALGORITHM:
    logger.error("CRITICAL: ALGORITHM environment variable is NOT SET.")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create OAuth2 scheme for token auth - set auto_error to False to prevent automatic exceptions
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# Create API key header for debug auth
#debug_header = APIKeyHeader(name="X-Debug-Auth", auto_error=False)

def verify_password(plain_password, hashed_password):
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create refresh JWT token with longer expiry"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Dependency to get current user from token"""
    logger.info(f"get_current_user: Attempting to validate token: {token[:20] if token else 'None'}...")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials - token processing issue",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        logger.warning("get_current_user: No token provided")
        raise credentials_exception
    
    if not SECRET_KEY or not ALGORITHM:
        logger.error("get_current_user: JWT_SECRET or ALGORITHM not configured!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT configuration error on server."
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        logger.info(f"get_current_user: Token decoded. Payload sub (user_id): {user_id}")
        
        if user_id is None:
            logger.warning("get_current_user: User ID (sub) not found in token payload.")
            raise credentials_exception
            
        user = db.exec(select(User).where(User.id == user_id)).first()
        
        if user is None:
            logger.warning(f"get_current_user: User with ID {user_id} not found in database.")
            raise credentials_exception
        
        logger.info(f"get_current_user: Successfully retrieved user {user.email} (ID: {user.id})")
        return user
    except JWTError as e:
        logger.error(f"get_current_user: JWTError during token decoding: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"get_current_user: Unexpected error: {str(e)}")
        raise credentials_exception

def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is active"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def get_owner_user(current_user: User = Depends(get_current_user)):
    """Ensure user has OWNER role"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def get_manager_user(current_user: User = Depends(get_current_user)):
    """Ensure user has at least MANAGER role"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if current_user.role not in [UserRole.OWNER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def get_current_user_from_supabase(request: Request):
    """Get current user from Supabase token"""
    token = get_token_from_header(request)
    if token:
        try:
            user = get_current_user(token)
            return user
        except Exception as e:
            logger.error(f"Error getting user from Supabase: {e}")
    return None

def get_current_active_user_from_supabase(request: Request):
    """Get current active user from Supabase token"""
    user = get_current_user_from_supabase(request)
    if user:
        return get_current_active_user(user)
    return None

def get_owner_user_from_supabase(request: Request):
    """Get owner user from Supabase token"""
    user = get_current_user_from_supabase(request)
    if user:
        return get_owner_user(user)
    return None

def get_manager_user_from_supabase(request: Request):
    """Get manager user from Supabase token"""
    user = get_current_user_from_supabase(request)
    if user:
        return get_manager_user(user)
    return None

def check_org_membership_and_permissions(
    current_user: User = Depends(get_current_user),
    operation_type: str = None,
    db: Session = Depends(get_db)
):
    """
    Unified permission check that validates:
    1. User has a valid organization_id
    2. User has appropriate role-based permissions for the requested operation
    
    operation_type: One of 'view_products', 'edit_products', 'view_suppliers',
                   'edit_suppliers', 'view_sales', 'edit_sales'
    """
    if not current_user:
        logger.error("check_org_membership_and_permissions: No current user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Checking permissions for user {current_user.email} (ID: {current_user.id}) - Role: {current_user.role.value}, Organization ID: {current_user.organization_id}, Operation: {operation_type}")
    
    # Check organization membership
    if current_user.organization_id is None:
        logger.error(f"User {current_user.email} does not belong to any organization")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to any organization"
        )
    
    # Owner has all permissions by default
    if current_user.role == UserRole.OWNER:
        logger.info(f"User {current_user.email} is OWNER - all permissions granted")
        return current_user
    
    # For staff and manager roles, we need to check rules
    if operation_type:
        rules = get_rules_by_organization_id(db, current_user.organization_id)
        
        if not rules:
            logger.warning(f"No rules found for organization {current_user.organization_id}")
            # Create default rules if none exist
            from app.api.mvp.rules import get_default_rules, create_rules
            default_rules = get_default_rules(current_user.role)
            logger.info(f"Creating default rules for organization {current_user.organization_id}")
            rules = create_rules(db, current_user.organization_id, default_rules)
            db.commit()
            db.refresh(rules)
        
        # Convert the role value to lowercase to match the Rules model's field naming
        role_prefix = current_user.role.value.lower()
        permission_attr = f"{role_prefix}_{operation_type}"
        
        logger.info(f"Checking permission attribute: {permission_attr}")
        
        # Check if the attribute exists in the rules model
        if hasattr(rules, permission_attr):
            has_permission = getattr(rules, permission_attr)
            logger.info(f"Permission check for {permission_attr}: {has_permission}")
            
            if not has_permission:
                logger.error(f"User {current_user.email} does not have permission for {operation_type}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail=f"User does not have permission for {operation_type}"
                )
        else:
            logger.error(f"Permission '{permission_attr}' not defined in rules model")
            # Log the available attributes in the rules model
            rules_attrs = [attr for attr in dir(rules) if not attr.startswith('_')]
            logger.error(f"Available attributes in rules model: {rules_attrs}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid permission check"
            )
    
    logger.info(f"Permission check passed for user {current_user.email}")
    return current_user 