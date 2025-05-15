from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from typing import Optional, Union, Dict, Any
from uuid import UUID
from sqlalchemy import select
from pydantic import BaseModel

from app.db.database import get_db
from app.api.mvp.auth import get_current_user, get_owner_user, get_manager_user
from app.api.auth.supabase import get_optional_supabase_user, get_token_from_header
from app.routers.supabase_auth import convert_role_to_enum
from app.api.mvp.rules import get_rules_by_user_id, create_rules, update_rules, delete_rules, generate_organization_id, get_default_rules
from app.schemas.data_models.Rules import RulesCreate, RulesUpdate, RulesRead
from app.models.data_models.User import User
from app.models.enums.UserRole import UserRole

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/rules",
    tags=["rules"],
    responses={404: {"description": "Not found"}},
)

# Define a new response model that includes organization_id from the User
class RulesReadWithOrg(RulesRead):
    organization_id: Optional[int] = None
    # We can make other fields from RulesRead explicit if needed, or rely on inheritance
    # For clarity, if RulesRead is simple, we could redefine all fields:
    # staff_view_products: bool
    # ... all other permission fields from RulesRead ...
    # user_id: UUID # Assuming RulesRead has user_id, if not, add it.

@router.get("/me", response_model=RulesReadWithOrg)
async def get_my_rules(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get rules for the current authenticated user, including their organization_id."""
    user = current_user
    
    if user is None:
        # Simplified auth block from previous versions - assuming this logic is sound
        try:
            supabase_user_data = await get_optional_supabase_user(request)
            if supabase_user_data:
                supabase_id = supabase_user_data.get("id")
                email = supabase_user_data.get("email")
                user = db.exec(select(User).where(User.supabase_id == supabase_id)).first()
                if not user and email:
                    user = db.exec(select(User).where(User.email == email)).first()
                    if user and supabase_id:
                        user.supabase_id = supabase_id # Link account
                        db.add(user)
                
                if not user and supabase_id and email: # Create user if not found
                    from app.routers.supabase_auth import SUPABASE_USER_PASSWORD_PLACEHOLDER
                    role = convert_role_to_enum(supabase_user_data.get("user_metadata", {}).get("role", "staff"))
                    user = User(email=email, supabase_id=supabase_id, password_hash=SUPABASE_USER_PASSWORD_PLACEHOLDER, role=role)
                    db.add(user)
                
                if user: # Commit any changes like linking or new user creation
                    db.commit()
                    db.refresh(user)
        except Exception as e:
            logger.error(f"Error during Supabase auth in GET /rules/me: {str(e)}")
            # Not raising HTTPException here to allow fallback to 401 if user is still None

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    rules = get_rules_by_user_id(db, user.id)
    
    if not rules:
        logger.info(f"No rules found for user {user.id}. Creating default rules.")
        # get_default_rules no longer takes organization_id
        default_rules_data = get_default_rules(user.role)
        rules = create_rules(db, user.id, default_rules_data)
        # User.organization_id must be handled here if it's a new user setting up org
        # This usually happens on POST, but GET might be the first time for a new Supabase user
        if user.organization_id is None: # If user has no org ID yet, generate one
            user.organization_id = generate_organization_id()
            logger.info(f"Generated organization_id {user.organization_id} for user {user.id} during GET /rules/me default rule creation.")
            db.add(user)
        
        db.commit() # Commit new rules and potentially new user.organization_id
        db.refresh(rules)
        if user: db.refresh(user) # Refresh user if modified

    # Populate the response model
    response_data = rules.dict() # Get dict from the Rules object
    response_data['organization_id'] = user.organization_id # Add user's org ID
    # Ensure all fields expected by RulesReadWithOrg are present
    # If RulesRead has user_id, it should be in rules.dict(). If not, and RulesReadWithOrg needs it, add: response_data['user_id'] = user.id 

    return RulesReadWithOrg(**response_data)

@router.post("/me", response_model=RulesReadWithOrg)
async def create_my_rules(
    request: Request,
    rules_data: RulesCreate,
    db: Session = Depends(get_db)
    # current_user: Optional[User] = Depends(get_current_user) # Temporarily remove direct dependency injection
):
    """Create or update rules for the current authenticated user. Manages User.organization_id."""
    
    user: Optional[User] = None
    token: Optional[str] = None
    is_new_user_session = False

    try:
        # Manually try to get the user
        token = get_token_from_header(request) # From app.api.auth.supabase, but it's a generic token extractor
        if not token:
            logger.warning("POST /rules/me: No token found in header.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated - no token")
        
        logger.info(f"POST /rules/me: Attempting to get user with token: {token[:20]}...")
        # Manually call get_current_user (it needs db explicitly passed if not using Depends for db in its own signature)
        # We need to ensure get_current_user is awaitable if it truly is async, or call it directly if not.
        # The definition was: async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        # So when calling manually, we pass token and db.
        user = await get_current_user(token=token, db=db) # Pass token and db session directly
        logger.info(f"POST /rules/me: Successfully called get_current_user. User: {user.email if user else 'None'}")

    except HTTPException as e: # Catch HTTPException from get_current_user or our no_token check
        logger.error(f"POST /rules/me: HTTPException during manual user retrieval: {e.detail}")
        # If it's the specific "Could not validate credentials - token processing issue" from get_current_user, it means get_current_user itself failed.
        # Re-raise it or a more generic one if needed
        if e.status_code == status.HTTP_401_UNAUTHORIZED and "token processing issue" in e.detail:
             # This indicates get_current_user internally failed as expected by its own logic
             pass # We will proceed to the supabase block as before
        else:
            raise e # Re-raise other HTTPErrors
    except Exception as e:
        logger.error(f"POST /rules/me: Unexpected error during manual user retrieval: {str(e)}")
        # Fall through to Supabase block or raise generic 500 if this is unexpected
        # For now, let's assume if this fails, user remains None and Supabase block is the fallback
        pass # User will be None

    # Authentication and user retrieval/creation block (Supabase fallback)
    if user is None:
        logger.info("POST /rules/me: User is None after initial token check, proceeding to Supabase auth flow.")
        try:
            supabase_user_data = await get_optional_supabase_user(request) 
            if supabase_user_data:
                supabase_id = supabase_user_data.get("id")
                email = supabase_user_data.get("email")
                logger.info(f"POST /rules/me: Supabase data found - ID: {supabase_id}, Email: {email}")
                # Try to find existing user by supabase_id or email
                if supabase_id:
                    user = db.exec(select(User).where(User.supabase_id == supabase_id)).first()
                if not user and email:
                    user = db.exec(select(User).where(User.email == email)).first()
                    if user and supabase_id and (not user.supabase_id or user.supabase_id != supabase_id):
                        logger.info(f"POST /rules/me: Linking existing user {email} to supabase_id {supabase_id}")
                        user.supabase_id = supabase_id 
                        db.add(user)
                
                if not user and supabase_id and email: # Create user if not found from Supabase data
                    from app.routers.supabase_auth import SUPABASE_USER_PASSWORD_PLACEHOLDER
                    role = convert_role_to_enum(supabase_user_data.get("user_metadata", {}).get("role", "staff"))
                    logger.info(f"POST /rules/me: Creating new user from Supabase data - Email: {email}, Role: {role}")
                    user = User(email=email, supabase_id=supabase_id, password_hash=SUPABASE_USER_PASSWORD_PLACEHOLDER, role=role)
                    db.add(user)
                    is_new_user_session = True 
            else:
                logger.warning("POST /rules/me: get_optional_supabase_user returned no data.")
        except Exception as e:
            logger.error(f"POST /rules/me: Error during Supabase auth/user processing: {str(e)}")

    if user is None:
        logger.error("POST /rules/me: Final user object is None after all auth attempts. Raising 401.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required - user not identified")

    if is_new_user_session or (user.id is None and user in db.new): # Check if user is new and needs commit for ID
        logger.info(f"POST /rules/me: Committing new user {user.email} to get ID before rules processing.")
        db.commit()
        db.refresh(user)
    elif user in db.dirty:
        logger.info(f"POST /rules/me: Committing changes for existing user {user.email} (e.g. supabase_id link) before rules processing.")
        db.commit()
        db.refresh(user)

    try:
        if user.organization_id is None:
            user.organization_id = generate_organization_id()
            logger.info(f"Generated new organization ID {user.organization_id} for user {user.id} in POST /rules/me.")
            db.add(user) 
        
        existing_rules = get_rules_by_user_id(db, user.id)
        rules_to_return = None
        
        if existing_rules:
            logger.info(f"Updating existing rules for user {user.id}.")
            rules_update_payload = RulesUpdate(**rules_data.dict(exclude_unset=True))
            rules_to_return = update_rules(db, user.id, rules_update_payload)
            if not rules_to_return:
                 raise HTTPException(status_code=500, detail="Failed to update rules.")
        else:
            logger.info(f"Creating new rules for user {user.id}.")
            rules_to_return = create_rules(db, user.id, rules_data)
        
        db.commit()
        logger.info(f"Committed rules and user updates for user {user.id}. User OrgID: {user.organization_id}")
        
        db.refresh(user)
        db.refresh(rules_to_return)

        response_data = rules_to_return.dict()
        response_data['organization_id'] = user.organization_id
        
        return RulesReadWithOrg(**response_data)

    except ValueError as e:
        logger.error(f"ValueError during rules processing for user {user.id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during POST /rules/me for user {user.id if user and user.id else 'Unknown'}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

@router.get("/{user_id}", response_model=RulesRead)
async def get_user_rules(
    user_id: UUID,
    current_user: User = Depends(get_manager_user),  # Only managers and owners can access other users' rules
    db: Session = Depends(get_db)
):
    """Get rules for a specific user (manager/owner only)"""
    rules = get_rules_by_user_id(db, user_id)
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rules not found"
        )
    
    return rules

@router.patch("/{user_id}", response_model=RulesRead)
async def update_user_rules(
    user_id: UUID,
    rules_data: RulesUpdate,
    current_user: User = Depends(get_owner_user),  # Only owners can update other users' rules
    db: Session = Depends(get_db)
):
    """Update rules for a specific user (owner only)"""
    rules = update_rules(db, user_id, rules_data)
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rules not found"
        )
    
    return rules

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_rules(
    user_id: UUID,
    current_user: User = Depends(get_owner_user),  # Only owners can delete rules
    db: Session = Depends(get_db)
):
    """Delete rules for a specific user (owner only)"""
    success = delete_rules(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rules not found"
        )
    
    return {"message": "Rules deleted successfully"} 