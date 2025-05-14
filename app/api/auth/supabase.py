from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
import base64
from typing import Optional, Dict, Any
from jose import jwt
from dotenv import load_dotenv
import logging

load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Debug mode for development - REMOVE IN PRODUCTION!
DEBUG_MODE = True

SUPABASE_URL = os.getenv("SUPABASE_URL", )
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET",)
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", )

SUPABASE_PROJECT_REF = SUPABASE_URL.split('.')[-2].split('/')[-1] if SUPABASE_URL else ""

security = HTTPBearer()

# Debug default user for development
DEBUG_DEFAULT_USER = {
    "id": "00000000-0000-0000-0000-000000000000",
    "email": "debug@example.com",
    "role": "owner"
}

def format_jwt_secret(jwt_secret: str) -> str:
    """Format JWT secret for decoding"""
    
    if not jwt_secret:
        return ""
        
    
    padding = 4 - (len(jwt_secret) % 4)
    if padding < 4:
        jwt_secret += "=" * padding
        
    
    try:
        decoded = base64.b64decode(jwt_secret).decode('utf-8')
        return decoded
    except Exception:
        return jwt_secret

async def fetch_supabase_user_info(token: str) -> dict:
    """Fetch user info from Supabase"""
    # If in debug mode and token is very short or malformed, return dummy user
    if DEBUG_MODE and (len(token) < 20 or token == "debug_token"):
        logger.warning("DEBUG MODE: Using fake user data for development")
        return DEBUG_DEFAULT_USER
        
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration is missing"
        )
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_ANON_KEY
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return response.json()

def verify_supabase_token(token: str) -> dict:
    """Verify Supabase JWT token"""
    # Debug mode bypass
    if DEBUG_MODE and (len(token) < 20 or token == "debug_token"):
        logger.warning("DEBUG MODE: Bypassing token verification")
        return {"sub": DEBUG_DEFAULT_USER["id"], "email": DEBUG_DEFAULT_USER["email"]}
        
    try:
        if not SUPABASE_JWT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase JWT secret is missing"
            )
        
        secret = format_jwt_secret(SUPABASE_JWT_SECRET)
        
        headers = jwt.get_unverified_header(token)
        
        unverified_claims = jwt.get_unverified_claims(token)
        token_type = unverified_claims.get("type", "")
        
        
        options = {
            "verify_signature": True,
            "verify_aud": True,
            "verify_exp": True
        }
        
        try:
            if token_type == "access":
                audience = "authenticated"
                payload = jwt.decode(
                    token, 
                    secret, 
                    algorithms=["HS256"], 
                    audience=audience,
                    options=options
                )
            elif token_type == "refresh":
                audience = SUPABASE_PROJECT_REF
                payload = jwt.decode(
                    token, 
                    secret, 
                    algorithms=["HS256"], 
                    audience=audience,
                    options=options
                )
            else:
                try:
                    payload = jwt.decode(
                        token, 
                        secret, 
                        algorithms=["HS256"], 
                        audience="authenticated",
                        options=options
                    )
                except Exception:
                    try:
                        payload = jwt.decode(
                            token, 
                            secret, 
                            algorithms=["HS256"], 
                            audience=SUPABASE_PROJECT_REF,
                            options=options
                        )
                    except Exception:
                        options["verify_aud"] = False
                        payload = jwt.decode(
                            token, 
                            secret, 
                            algorithms=["HS256"], 
                            options=options
                        )
        except Exception as jwt_error:
            options["verify_aud"] = False 
            payload = jwt.decode(
                token, 
                SUPABASE_JWT_SECRET, 
                algorithms=["HS256"], 
                options=options
            )
            
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

async def get_supabase_user(request: Request) -> Dict[str, Any]:
    """Get and validate the Supabase user from the Authorization header"""
    if DEBUG_MODE:
        # Check for debug header
        debug_header = request.headers.get("X-Debug-Auth")
        if debug_header == "true":
            logger.warning("DEBUG MODE: Bypassing authentication with debug header")
            return DEBUG_DEFAULT_USER
    
    if "Authorization" not in request.headers:
        if DEBUG_MODE:
            logger.warning("DEBUG MODE: No auth header, using default debug user")
            return DEBUG_DEFAULT_USER
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided"
        )
    
    auth_header = request.headers.get("Authorization")
    if not auth_header.startswith("Bearer "):
        if DEBUG_MODE:
            logger.warning("DEBUG MODE: Invalid auth scheme, using default debug user")
            return DEBUG_DEFAULT_USER
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )
    
    token = auth_header.replace("Bearer ", "")
    
    if not token:
        if DEBUG_MODE:
            logger.warning("DEBUG MODE: Empty token, using default debug user")
            return DEBUG_DEFAULT_USER
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )
    
    try:
        user_info = await fetch_supabase_user_info(token)
        return user_info
    except HTTPException:
        if DEBUG_MODE:
            logger.warning("DEBUG MODE: Authentication error, using default debug user")
            return DEBUG_DEFAULT_USER
        raise
    except Exception as e:
        if DEBUG_MODE:
            logger.warning(f"DEBUG MODE: Error validating token: {str(e)}, using default debug user")
            return DEBUG_DEFAULT_USER
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error validating token: {str(e)}"
        )

async def get_current_supabase_user(request: Request) -> Dict[str, Any]:
    """Dependency to get the current Supabase user"""
    return await get_supabase_user(request)

async def get_optional_supabase_user(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency to get the current Supabase user, but don't raise an exception if not authenticated"""
    try:
        return await get_supabase_user(request)
    except HTTPException:
        return None

async def cleanup_user_session(supabase_id: str) -> None:
    """
    Args:
        supabase_id: The Supabase user ID
    """
   
    pass 