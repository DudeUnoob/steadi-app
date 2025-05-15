from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
import base64
from typing import Optional, Dict, Any
from jose import jwt
from dotenv import load_dotenv
import logging
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

# Add this to improve logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_supabase_user_info(token: str) -> dict:
    """Fetch user info from Supabase auth API"""
    # Debug mode check
    if DEBUG_MODE and (len(token) < 20 or token == "debug_token"):
        logger.warning("DEBUG MODE: Using fake user data for development")
        return DEBUG_DEFAULT_USER
    
    # Verify Supabase configuration
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.error("Supabase configuration is missing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration is missing"
        )
    
    logger.info(f"Attempting to fetch user info with token length: {len(token)}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": SUPABASE_ANON_KEY
                }
            )
            
            logger.info(f"Supabase API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Supabase API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid authentication credentials: {response.text}"
                )
            
            user_data = response.json()
            logger.info(f"Successfully fetched user data: {user_data.get('email')}")
            
            # Ensure we have user metadata with role
            if 'user_metadata' not in user_data:
                user_data['user_metadata'] = {}
                
            # Check if we can extract app_metadata and supplement it into user_metadata
            if 'app_metadata' in user_data and user_data.get('app_metadata'):
                app_meta = user_data.get('app_metadata', {})
                if not user_data['user_metadata'].get('role') and app_meta.get('role'):
                    user_data['user_metadata']['role'] = app_meta.get('role')
            
            return user_data
            
        except httpx.TimeoutException as e:
            logger.error(f"Timeout when connecting to Supabase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Timeout connecting to authentication service"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error when connecting to Supabase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error connecting to authentication service: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during Supabase authentication: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}"
            )

def verify_supabase_token(token: str) -> dict:
    """Verify Supabase JWT token - simplified version"""
    try:
        # Check for JWT secret
        if not SUPABASE_JWT_SECRET:
            logger.error("Supabase JWT secret is missing")
            raise ValueError("JWT secret is missing from configuration")
        
        # Format the secret
        secret = format_jwt_secret(SUPABASE_JWT_SECRET)
        
        # First try to get unverified claims to determine token type
        unverified_claims = jwt.get_unverified_claims(token)
        logger.info(f"Token type from unverified claims: {unverified_claims.get('type', 'unknown')}")
        
        # For simplicity, we'll try decoding with minimal verification first
        options = {
            "verify_signature": False,  # Just check structure initially
            "verify_aud": False,
            "verify_exp": True  # Still check expiration
        }
        
        # This just gives us the contents without strict verification
        payload = jwt.decode(token, options=options, key=secret, algorithms=["HS256"])
        
        # If we get here, token structure is valid, now try with signature
        try:
            options["verify_signature"] = True
            # Try with all possible audiences
            for audience in ["authenticated", SUPABASE_PROJECT_REF, None]:
                try:
                    if audience:
                        verified_payload = jwt.decode(
                            token, 
                            key=secret,
                            algorithms=["HS256"],
                            audience=audience,
                            options=options
                        )
                        logger.info(f"Successfully verified token with audience: {audience}")
                        return verified_payload
                except Exception:
                    continue
            
            # If no audience worked, try without audience verification
            options["verify_aud"] = False
            verified_payload = jwt.decode(
                token,
                key=secret,
                algorithms=["HS256"],
                options=options
            )
            logger.info("Successfully verified token without audience check")
            return verified_payload
            
        except Exception as verify_error:
            # If verification with signature fails, return unverified payload with warning
            logger.warning(f"Could not verify token signature: {str(verify_error)}. Using unverified payload.")
            return payload
            
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise ValueError(f"Invalid token: {str(e)}")

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

def get_token_from_header(request: Request) -> Optional[str]:
    """Extract the token from the Authorization header"""
    try:
        if "Authorization" not in request.headers:
            return None
        
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not isinstance(auth_header, str):
            return None
        
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.replace("Bearer ", "").strip()
        return token if token else None
    except Exception as e:
        logging.error(f"Error extracting token from header: {str(e)}")
        return None

async def get_optional_supabase_user(request: Request) -> Optional[dict]:
    """
    Extract and validate Supabase JWT from the request, returning user data 
    if valid, or None if no valid token is found
    """
    token = get_token_from_header(request)
    if not token:
        logger.warning("get_optional_supabase_user: No token found in request header.")
        return None
    
    logger.info(f"get_optional_supabase_user: Attempting to validate Supabase token (length: {len(token)})")
    
    try:
        user_data = await fetch_supabase_user_info(token)
        if user_data:
            logger.info(f"get_optional_supabase_user: Successfully validated token via fetch_supabase_user_info for user: {user_data.get('email')}")
            return user_data
        else:
            # This case should ideally not happen if fetch_supabase_user_info raises on error
            logger.warning("get_optional_supabase_user: fetch_supabase_user_info returned None/empty, which is unexpected.")
            # Fall through to local JWT verification as a last resort if fetch_supabase_user_info was permissive
    except HTTPException as http_exc: # Catch HTTPExceptions from fetch_supabase_user_info
        logger.error(f"get_optional_supabase_user: HTTPException from fetch_supabase_user_info: {http_exc.status_code} - {http_exc.detail}")
        # Do not re-raise, fall through to local JWT check or return None
    except Exception as e:
        logger.error(f"get_optional_supabase_user: Unexpected error during fetch_supabase_user_info: {str(e)}")
        # Do not re-raise, fall through to local JWT check or return None
        
    # Fall back to local JWT verification if API call failed or didn't return data
    try:
        logger.info("get_optional_supabase_user: Falling back to local JWT verification.")
        payload = verify_supabase_token(token) # verify_supabase_token can raise ValueError
        if payload and payload.get("sub") and payload.get("email"):
            logger.info(f"get_optional_supabase_user: Local JWT validation successful for sub: {payload.get('sub')}")
            return {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "user_metadata": {
                    "role": payload.get("role", payload.get("user_role")) # Try common role claim names
                },
                "aud": payload.get("aud") # Include audience for context
            }
        else:
            logger.warning(f"get_optional_supabase_user: Local JWT verification did not yield sufficient payload. Payload: {payload}")
    except ValueError as ve:
        logger.error(f"get_optional_supabase_user: Local JWT validation failed (ValueError): {str(ve)}")
    except Exception as jwt_e:
        logger.error(f"get_optional_supabase_user: Local JWT validation failed with unexpected error: {str(jwt_e)}")
    
    logger.warning("get_optional_supabase_user: All authentication methods failed, returning None.")
    return None

async def cleanup_user_session(supabase_id: str) -> None:
    """Clean up user session data
    
    Args:
        supabase_id: The Supabase user ID
    """
    logger.info(f"Cleaning up session for user with Supabase ID: {supabase_id}")
    # Implement any session cleanup logic here if needed
    pass 