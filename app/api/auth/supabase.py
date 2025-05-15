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

# Debug mode for development - set to False in production
DEBUG_MODE = False

# Supabase configuration - strip whitespace to handle formatting issues
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "").strip().replace(" ", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip().replace(" ", "")

# Extract project reference from URL
SUPABASE_PROJECT_REF = SUPABASE_URL.split('.')[-2].split('/')[-1] if SUPABASE_URL else ""

# Log configuration for diagnostics
logger.info(f"Supabase URL: {SUPABASE_URL}")
logger.info(f"Supabase Project Ref: {SUPABASE_PROJECT_REF}")
logger.info(f"Supabase JWT Secret length: {len(SUPABASE_JWT_SECRET)} chars")
logger.info(f"Supabase Anon Key length: {len(SUPABASE_ANON_KEY)} chars")

security = HTTPBearer()

# Debug default user for development only
DEBUG_DEFAULT_USER = {
    "id": "00000000-0000-0000-0000-000000000000",
    "email": "debug@example.com",
    "role": "owner"
}

def format_jwt_secret(jwt_secret: str) -> str:
    """Format JWT secret for decoding"""
    if not jwt_secret:
        logger.error("JWT secret is empty")
        return ""
    
    # Add padding if needed
    padding = 4 - (len(jwt_secret) % 4)
    if padding < 4:
        jwt_secret += "=" * padding
    
    try:
        # Attempt to decode base64
        decoded = base64.b64decode(jwt_secret).decode('utf-8')
        logger.debug("Successfully formatted JWT secret")
        return decoded
    except Exception as e:
        logger.warning(f"Error formatting JWT secret: {str(e)}, using original")
        return jwt_secret

async def fetch_supabase_user_info(token: str) -> dict:
    """Fetch user info from Supabase auth API"""
    # Debug mode check
    if DEBUG_MODE and (len(token) < 20 or token == "debug_token"):
        logger.warning("DEBUG MODE: Using fake user data for development")
        return DEBUG_DEFAULT_USER
    
    # Verify Supabase configuration
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.error("Supabase configuration missing: URL or Anon Key")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration is missing"
        )
    
    # Make request to Supabase Auth API
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Fetching user info from {SUPABASE_URL}/auth/v1/user")
            response = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": SUPABASE_ANON_KEY
                }
            )
            
            # Log response status for debugging
            logger.info(f"Supabase auth response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Supabase auth error: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            
            user_data = response.json()
            logger.info(f"Successfully retrieved user data for {user_data.get('email', 'unknown')}")
            return user_data
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Supabase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error connecting to authentication service: {str(e)}"
        )

def verify_supabase_token(token: str) -> dict:
    """Verify Supabase JWT token"""
    # Debug mode bypass
    if DEBUG_MODE and (len(token) < 20 or token == "debug_token"):
        logger.warning("DEBUG MODE: Bypassing token verification")
        return {"sub": DEBUG_DEFAULT_USER["id"], "email": DEBUG_DEFAULT_USER["email"]}
    
    try:
        # Check for JWT secret
        if not SUPABASE_JWT_SECRET:
            logger.error("Supabase JWT secret is missing")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase JWT secret is missing"
            )
        
        # Format secret
        secret = format_jwt_secret(SUPABASE_JWT_SECRET)
        
        # Get token header
        headers = jwt.get_unverified_header(token)
        logger.debug(f"Token headers: {headers}")
        
        # Get unverified claims to check token type
        unverified_claims = jwt.get_unverified_claims(token)
        token_type = unverified_claims.get("type", "")
        logger.debug(f"Token type: {token_type}")
        
        # JWT decode options
        options = {
            "verify_signature": True,
            "verify_aud": True,
            "verify_exp": True
        }
        
        # Decode token based on type
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
                # Try different audience values if token type is not specified
                try:
                    payload = jwt.decode(
                        token, 
                        secret, 
                        algorithms=["HS256"], 
                        audience="authenticated",
                        options=options
                    )
                except Exception as e1:
                    logger.debug(f"Failed to decode with 'authenticated' audience: {str(e1)}")
                    try:
                        payload = jwt.decode(
                            token, 
                            secret, 
                            algorithms=["HS256"], 
                            audience=SUPABASE_PROJECT_REF,
                            options=options
                        )
                    except Exception as e2:
                        logger.debug(f"Failed to decode with project ref audience: {str(e2)}")
                        # Try without audience verification
                        options["verify_aud"] = False
                        payload = jwt.decode(
                            token, 
                            secret, 
                            algorithms=["HS256"], 
                            options=options
                        )
        except Exception as jwt_error:
            logger.debug(f"JWT decode error, trying without audience: {str(jwt_error)}")
            # Last resort - try without audience verification
            options["verify_aud"] = False 
            payload = jwt.decode(
                token, 
                secret,  # Use formatted secret
                algorithms=["HS256"], 
                options=options
            )
            
        logger.info(f"Successfully verified token for user ID: {payload.get('sub', 'unknown')}")
        return payload
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

async def get_supabase_user(request: Request) -> Dict[str, Any]:
    """Get and validate the Supabase user from the Authorization header"""
    # Debug mode check
    if DEBUG_MODE:
        # Check for debug header
        debug_header = request.headers.get("X-Debug-Auth")
        if debug_header == "true":
            logger.warning("DEBUG MODE: Bypassing authentication with debug header")
            return DEBUG_DEFAULT_USER
    
    # Check for Authorization header
    if "Authorization" not in request.headers:
        if DEBUG_MODE:
            logger.warning("DEBUG MODE: No auth header, using default debug user")
            return DEBUG_DEFAULT_USER
        
        logger.error("No authentication credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided"
        )
    
    # Parse Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header.startswith("Bearer "):
        if DEBUG_MODE:
            logger.warning("DEBUG MODE: Invalid auth scheme, using default debug user")
            return DEBUG_DEFAULT_USER
        
        logger.error("Invalid authentication scheme")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )
    
    # Extract token
    token = auth_header.replace("Bearer ", "").strip()
    
    if not token:
        if DEBUG_MODE:
            logger.warning("DEBUG MODE: Empty token, using default debug user")
            return DEBUG_DEFAULT_USER
        
        logger.error("No token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )
    
    try:
        # Fetch user info from Supabase
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
        
        logger.error(f"Error validating token: {str(e)}")
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
    """Clean up user session data
    
    Args:
        supabase_id: The Supabase user ID
    """
    logger.info(f"Cleaning up session for user with Supabase ID: {supabase_id}")
    # Implement any session cleanup logic here if needed
    pass 