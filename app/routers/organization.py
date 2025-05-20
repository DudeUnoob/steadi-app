from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from app.db.database import get_db
from app.api.mvp.auth import get_current_user, get_owner_user, get_manager_user
from app.models.data_models.User import User
from app.models.enums.UserRole import UserRole
from app.models.service_classes.OrganizationService import OrganizationService

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
    responses={404: {"description": "Not found"}},
)

class UserInOrg(BaseModel):
    id: UUID
    email: str
    role: UserRole
    
    class Config:
        orm_mode = True

class ChangeRoleRequest(BaseModel):
    user_id: UUID
    role: UserRole

@router.get("/users", response_model=List[UserInOrg])
async def get_organization_users(
    request: Request,
    current_user: User = Depends(get_manager_user),  # Manager or owner can see users
    db: Session = Depends(get_db)
):
    """Get all users in the current user's organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not part of an organization"
        )
    
    org_service = OrganizationService(db)
    users = org_service.get_organization_users(current_user.organization_id)
    
    if isinstance(users, dict) and "error" in users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=users["error"]
        )
    
    return users

@router.post("/users/{user_id}", response_model=User)
async def add_user_to_organization(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(get_owner_user),  # Only owner can add users
    db: Session = Depends(get_db)
):
    """Add a user to the current user's organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not part of an organization"
        )
    
    org_service = OrganizationService(db)
    result = org_service.add_user_to_organization(user_id, current_user.organization_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.delete("/users/{user_id}", response_model=Dict[str, str])
async def remove_user_from_organization(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(get_owner_user),  # Only owner can remove users
    db: Session = Depends(get_db)
):
    """Remove a user from the current user's organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not part of an organization"
        )
    
    # Prevent removing self
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from your organization"
        )
    
    org_service = OrganizationService(db)
    result = org_service.remove_user_from_organization(user_id, current_user.organization_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.put("/users/role", response_model=User)
async def change_user_role(
    request: Request,
    role_request: ChangeRoleRequest,
    current_user: User = Depends(get_owner_user),  # Only owner can change roles
    db: Session = Depends(get_db)
):
    """Change a user's role in the current user's organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not part of an organization"
        )
    
    # Prevent changing own role
    if role_request.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role"
        )
    
    org_service = OrganizationService(db)
    result = org_service.change_user_role(
        role_request.user_id, 
        current_user.organization_id, 
        role_request.role
    )
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/code", response_model=Dict[str, int])
async def get_organization_code(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the organization code for the current user"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not part of an organization"
        )
    
    return {"organization_code": current_user.organization_id} 