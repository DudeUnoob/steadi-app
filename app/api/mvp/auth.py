from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.db.database import get_db
from app.models.data_models.User import User
from app.models.enums.UserRole import UserRole
import logging
import os


SECRET_KEY = os.getenv("JWT_SECRET", )
ALGORITHM = os.getenv("ALGORITHM", )
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", ))

# Debug mode for development - REMOVE IN PRODUCTION!
DEBUG_MODE = True
logger = logging.getLogger(__name__)

# Debug default user data
DEBUG_USER_ID = "11111111-1111-1111-1111-111111111111"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

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

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), request: Request = None):
    """Dependency to get current user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Debug mode: check for special headers
    if DEBUG_MODE and request:
        debug_header = request.headers.get("X-Debug-Auth")
        if debug_header == "true":
            logger.warning("DEBUG MODE: Bypassing token validation, using debug user")
            debug_user = db.exec(select(User).where(User.id == DEBUG_USER_ID)).first()
            if debug_user:
                return debug_user
            else:
                # Create a debug user if it doesn't exist
                new_debug_user = User(
                    id=DEBUG_USER_ID,
                    email="debug@test.com",
                    password_hash="DEBUG_USER",
                    role=UserRole.OWNER,
                    supabase_id="11111111-1111-1111-1111-111111111111"
                )
                db.add(new_debug_user)
                db.commit()
                db.refresh(new_debug_user)
                return new_debug_user
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        
        user = db.exec(select(User).where(User.id == user_id)).first()
        if user is None:
            raise credentials_exception
            
        return user
    except JWTError:
        raise credentials_exception

def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is active"""
    return current_user


def get_owner_user(current_user: User = Depends(get_current_user)):
    """Ensure user has OWNER role"""
    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def get_manager_user(current_user: User = Depends(get_current_user)):
    """Ensure user has at least MANAGER role"""
    if current_user.role not in [UserRole.OWNER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user 