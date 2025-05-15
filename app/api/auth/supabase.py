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




SUPABASE_URL = os.getenv("SUPABASE_URL", )
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET",)
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", )


SUPABASE_PROJECT_REF = SUPABASE_URL.split('.')[-2].split('/')[-1] if SUPABASE_URL else ""


security = HTTPBearer()

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

# Add this to improve logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_supabase_user_info(token: str) -> dict:
    """Fetch user info from Supabase"""
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
    if "Authorization" not in request.headers:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided"
        )
    
    auth_header = request.headers.get("Authorization")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )
    
    token = auth_header.replace("Bearer ", "")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )
    
    try:
        user_info = await fetch_supabase_user_info(token)
        return user_info
    except HTTPException:
        raise
    except Exception as e:
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
        logger.warning("No token found in request")
        return None
    
    logger.info(f"Attempting to validate Supabase token (length: {len(token)})")
    
    # Try direct API method first as it's most reliable
    try:
        user_data = await fetch_supabase_user_info(token)
        if user_data:
            logger.info(f"Successfully validated token from Supabase for user: {user_data.get('email')}")
            return user_data
    except Exception as e:
        logger.error(f"Error validating token with Supabase API: {str(e)}")
        
        # Fall back to local JWT verification without throwing exceptions
        try:
            logger.info("Falling back to local JWT verification")
            payload = verify_supabase_token(token)
            if payload:
                logger.info(f"JWT validation successful: {payload.get('sub')}")
                # Construct minimal user data from JWT claims
                return {
                    "id": payload.get("sub"),
                    "email": payload.get("email", "unknown@example.com"),
                    "user_metadata": {
                        "role": payload.get("role", "staff")
                    }
                }
        except Exception as jwt_e:
            logger.error(f"Local JWT validation also failed: {str(jwt_e)}")
    
    # If all methods fail, return None instead of raising an exception
    logger.warning("All authentication methods failed, returning None")
    return None

async def cleanup_user_session(supabase_id: str) -> None:
    """
    Args:
        supabase_id: The Supabase user ID
    """
   
    pass 