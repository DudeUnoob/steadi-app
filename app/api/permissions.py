from fastapi import Depends, HTTPException, status, Request
from sqlmodel import Session, select
from uuid import UUID
from typing import Callable, Optional, List
import logging

from app.db.database import get_db
from app.models.data_models.User import User
from app.models.data_models.Rules import Rules
from app.models.enums.UserRole import UserRole
from app.api.mvp.auth import get_current_user, get_authenticated_user
from app.api.mvp.rules import get_rules_by_user_id

logger = logging.getLogger(__name__)

async def check_permission(
    request: Request,
    permission_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Check if a user has a specific permission.
    
    This is a generic dependency function that can be used to protect routes
    based on specific permissions defined in the Rules table.
    
    Args:
        request: The request object
        permission_name: The name of the permission to check (e.g., "staff_view_products")
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The user if they have the required permission
        
    Raises:
        HTTPException: If the user doesn't have the required permission
    """
    # OWNER role has all permissions
    if current_user.role == UserRole.OWNER:
        return current_user
    
    # Get the user's rules
    rules = get_rules_by_user_id(db, current_user.id)
    
    if not rules:
        logger.error(f"No rules found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )
    
    # Check if permission exists in the Rules model
    if not hasattr(rules, permission_name):
        logger.error(f"Permission {permission_name} not found in Rules model")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid permission check"
        )
    
    # Check if the user has the required permission
    if not getattr(rules, permission_name):
        logger.warning(f"User {current_user.id} denied access: missing {permission_name}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )
    
    return current_user

# Specific permission checker factory functions
def require_view_products():
    """
    Dependency to check if a user can view products.
    Usage: @router.get("/products", dependencies=[Depends(require_view_products())])
    """
    async def check_view_products(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if current_user.role == UserRole.OWNER:
            return current_user
        elif current_user.role == UserRole.MANAGER:
            return await check_permission(request, "manager_view_products", current_user, db)
        else:
            return await check_permission(request, "staff_view_products", current_user, db)
    
    return check_view_products

def require_edit_products():
    """
    Dependency to check if a user can edit products.
    Usage: @router.post("/products", dependencies=[Depends(require_edit_products())])
    """
    async def check_edit_products(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if current_user.role == UserRole.OWNER:
            return current_user
        elif current_user.role == UserRole.MANAGER:
            return await check_permission(request, "manager_edit_products", current_user, db)
        else:
            return await check_permission(request, "staff_edit_products", current_user, db)
    
    return check_edit_products

def require_view_suppliers():
    """
    Dependency to check if a user can view suppliers.
    Usage: @router.get("/suppliers", dependencies=[Depends(require_view_suppliers())])
    """
    async def check_view_suppliers(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if current_user.role == UserRole.OWNER:
            return current_user
        elif current_user.role == UserRole.MANAGER:
            return await check_permission(request, "manager_view_suppliers", current_user, db)
        else:
            return await check_permission(request, "staff_view_suppliers", current_user, db)
    
    return check_view_suppliers

def require_edit_suppliers():
    """
    Dependency to check if a user can edit suppliers.
    Usage: @router.post("/suppliers", dependencies=[Depends(require_edit_suppliers())])
    """
    async def check_edit_suppliers(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if current_user.role == UserRole.OWNER:
            return current_user
        elif current_user.role == UserRole.MANAGER:
            return await check_permission(request, "manager_edit_suppliers", current_user, db)
        else:
            return await check_permission(request, "staff_edit_suppliers", current_user, db)
    
    return check_edit_suppliers

def require_view_sales():
    """
    Dependency to check if a user can view sales.
    Usage: @router.get("/sales", dependencies=[Depends(require_view_sales())])
    """
    async def check_view_sales(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if current_user.role == UserRole.OWNER:
            return current_user
        elif current_user.role == UserRole.MANAGER:
            return await check_permission(request, "manager_view_sales", current_user, db)
        else:
            return await check_permission(request, "staff_view_sales", current_user, db)
    
    return check_view_sales

def require_edit_sales():
    """
    Dependency to check if a user can edit sales.
    Usage: @router.post("/sales", dependencies=[Depends(require_edit_sales())])
    """
    async def check_edit_sales(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if current_user.role == UserRole.OWNER:
            return current_user
        elif current_user.role == UserRole.MANAGER:
            return await check_permission(request, "manager_edit_sales", current_user, db)
        else:
            return await check_permission(request, "staff_edit_sales", current_user, db)
    
    return check_edit_sales

def require_set_staff_rules():
    """
    Dependency to check if a user can set staff rules.
    Usage: @router.post("/rules/{user_id}", dependencies=[Depends(require_set_staff_rules())])
    """
    async def check_set_staff_rules(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if current_user.role == UserRole.OWNER:
            return current_user
        elif current_user.role == UserRole.MANAGER:
            return await check_permission(request, "manager_set_staff_rules", current_user, db)
        else:
            # Staff members shouldn't be able to set staff rules at all
            logger.warning(f"Staff user {current_user.id} attempted to set staff rules")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to set staff rules"
            )
    
    return check_set_staff_rules