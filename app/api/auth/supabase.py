from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
import base64
from typing import Optional
from jose import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase settings


SUPABASE_URL = os.getenv("SUPABASE_URL", 'https://qciebchpdjxfumeoafwt.supabase.co')
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "IdC20ZzBxumt9t1D3YOr6XVnVM7dmIWn0bfU+NSDhgl8MZjClnQiYsFXSmL0ywk/b0wnN9Jp3ZFLlLzkGEv4uw==")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjaWViY2hwZGp4ZnVtZW9hZnd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NDc2NTMsImV4cCI6MjA2MjMyMzY1M30.7hihI8t5_z7YFX_Yp9R4FgJYUvSFEOYix73Un-tWA0Y')

# Extract project reference from URL (used for audience validation)
SUPABASE_PROJECT_REF = SUPABASE_URL.split('.')[-2].split('/')[-1] if SUPABASE_URL else ""

# HTTP bearer token scheme
security = HTTPBearer()

def format_jwt_secret(jwt_secret: str) -> str:
    """Format JWT secret for decoding"""
    # Supabase JWT secrets are base64 encoded
    # We need to ensure it's properly padded
    if not jwt_secret:
        return ""
        
    # Add padding if needed
    padding = 4 - (len(jwt_secret) % 4)
    if padding < 4:
        jwt_secret += "=" * padding
        
    # Decode and return as string
    try:
        decoded = base64.b64decode(jwt_secret).decode('utf-8')
        return decoded
    except Exception:
        # If there's an error, return the original string
        return jwt_secret

async def fetch_supabase_user_info(token: str) -> dict:
    """Fetch user info from Supabase"""
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
    try:
        if not SUPABASE_JWT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase JWT secret is missing"
            )
        
        # Format the JWT secret for proper decoding
        secret = format_jwt_secret(SUPABASE_JWT_SECRET)
        
        # Get token header without verification to check token type
        headers = jwt.get_unverified_header(token)
        
        # Extract expected audience from token without verification
        # This helps us determine if it's an access token or refresh token
        unverified_claims = jwt.get_unverified_claims(token)
        token_type = unverified_claims.get("type", "")
        
        # Different token types have different audience expectations
        # Access tokens: aud = "authenticated"
        # Refresh tokens: aud = project reference
        
        # Set options for JWT decoding
        options = {
            "verify_signature": True,
            "verify_aud": True,
            "verify_exp": True
        }
        
        try:
            # For access tokens (most common)
            if token_type == "access":
                audience = "authenticated"
                payload = jwt.decode(
                    token, 
                    secret, 
                    algorithms=["HS256"], 
                    audience=audience,
                    options=options
                )
            # For refresh tokens
            elif token_type == "refresh":
                audience = SUPABASE_PROJECT_REF
                payload = jwt.decode(
                    token, 
                    secret, 
                    algorithms=["HS256"], 
                    audience=audience,
                    options=options
                )
            # If we can't determine token type, try without audience validation
            else:
                # Try with different common audience values
                try:
                    # First try with "authenticated" audience
                    payload = jwt.decode(
                        token, 
                        secret, 
                        algorithms=["HS256"], 
                        audience="authenticated",
                        options=options
                    )
                except Exception:
                    # Then try with project reference as audience
                    try:
                        payload = jwt.decode(
                            token, 
                            secret, 
                            algorithms=["HS256"], 
                            audience=SUPABASE_PROJECT_REF,
                            options=options
                        )
                    except Exception:
                        # As a last resort, skip audience validation
                        options["verify_aud"] = False
                        payload = jwt.decode(
                            token, 
                            secret, 
                            algorithms=["HS256"], 
                            options=options
                        )
        except Exception as jwt_error:
            # If using the formatted secret fails, try with the original JWT secret
            options["verify_aud"] = False  # Skip audience validation as a fallback
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

async def get_current_supabase_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current Supabase user from token"""
    token = credentials.credentials
    
    # Verify token
    payload = verify_supabase_token(token)
    
    # Fetch user information
    user_info = await fetch_supabase_user_info(token)
    
    return user_info

async def get_optional_supabase_user(request: Request) -> Optional[dict]:
    """Get optional Supabase user from token (doesn't throw if no token)"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    
    try:
        # Verify token
        payload = verify_supabase_token(token)
        
        # Fetch user information
        user_info = await fetch_supabase_user_info(token)
        
        return user_info
    except HTTPException:
        return None 