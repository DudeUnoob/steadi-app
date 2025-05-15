from datetime import datetime, timedelta
from typing import Optional, Callable
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlmodel import Session, select
from app.db.database import get_db
from app.models.data_models.User import User
from app.models.enums.UserRole import UserRole
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Clean and sanitize environment variables
SECRET_KEY = os.getenv("JWT_SECRET", "supersecret").strip()
ALGORITHM = os.getenv("ALGORITHM", "HS256").strip()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30").strip())

# Log JWT configuration for diagnostics
logger = logging.getLogger(__name__)
logger.info(f"JWT ALGORITHM: {ALGORITHM}")
logger.info(f"JWT SECRET KEY length: {len(SECRET_KEY)} chars")
logger.info(f"JWT TOKEN EXPIRY: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")

# Debug mode for development - set to False in production
DEBUG_MODE = False

# Debug default user data
DEBUG_USER_ID = "11111111-1111-1111-1111-111111111111"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create OAuth2 scheme for token auth - set auto_error to False to prevent automatic exceptions
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# Create API key header for debug auth
debug_header = APIKeyHeader(name="X-Debug-Auth", auto_error=False)

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

def get_debug_user(db: Session):
    """Get or create a debug user for development purposes"""
    logger.warning("DEBUG MODE: Using debug user")
    debug_user = db.exec(select(User).where(User.id == DEBUG_USER_ID)).first()
    if debug_user:
        return debug_user
    else:
        # Create a debug user if it doesn't exist
        logger.warning("DEBUG MODE: Creating debug user")
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

async def get_current_user(
    request: Request = None,
    token: str = Depends(oauth2_scheme),
    debug_key: str = Security(debug_header),
    db: Session = Depends(get_db)
):
    """
    Dependency to get current user from token or debug header
    Returns None if authentication fails instead of raising an exception
    when used with combined auth flows.
    """
    # Debug mode: check for special headers first
    if DEBUG_MODE:
        # Check if debug header is set directly via Security dependency
        if debug_key == "true":
            return get_debug_user(db)
            
        # Also check the request headers as a fallback
        if request and request.headers.get("X-Debug-Auth") == "true":
            return get_debug_user(db)
    
    # No debug auth, so try normal token auth
    if not token:
        logger.debug("No JWT token provided")
        return None
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.debug("JWT token missing subject claim")
            return None
            
        user = db.exec(select(User).where(User.id == user_id)).first()
        if user is None:
            logger.debug(f"User with ID {user_id} from JWT token not found in database")
            return None
        
        logger.info(f"Successfully authenticated user {user.email} via JWT token")
        return user
    except JWTError as e:
        logger.debug(f"JWT validation error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during JWT authentication: {str(e)}")
        return None

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