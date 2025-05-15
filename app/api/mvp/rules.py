from typing import Optional, List
from sqlmodel import Session, select
from app.models.data_models.Rules import Rules
from app.models.data_models.User import User
from app.schemas.data_models.Rules import RulesCreate, RulesUpdate
from app.models.enums.UserRole import UserRole
from uuid import UUID
import random
import logging

logger = logging.getLogger(__name__)

def get_rules_by_user_id(db: Session, user_id: UUID) -> Optional[Rules]:
    """Get rules for a specific user"""
    return db.exec(select(Rules).where(Rules.user_id == user_id)).first()

def create_rules(db: Session, user_id: UUID, rules_data: RulesCreate) -> Rules:
    """Create new rules for a user. Assumes rules do not already exist based on router logic."""
    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        # This case should ideally be caught by the router before calling this
        raise ValueError(f"User with ID {user_id} not found for creating rules")
    
    # Create new rules object. organization_id is no longer part of RulesCreate or Rules model.
    rules = Rules(user_id=user_id, **rules_data.dict(exclude_unset=True))
    
    db.add(rules) # Add rules to session for commit by router
    # db.commit() and db.refresh() are handled by the router
    
    return rules

def update_rules(db: Session, user_id: UUID, rules_data: RulesUpdate) -> Optional[Rules]:
    """Update existing rules for a user"""
    rules = get_rules_by_user_id(db, user_id)
    if not rules:
        return None
    
    # organization_id is no longer part of RulesUpdate or Rules model.
    rules_dict = rules_data.dict(exclude_unset=False) 

    for key, value in rules_dict.items():
        setattr(rules, key, value)
    
    db.add(rules) # Add rules to session for commit by router
    # db.commit() and db.refresh() are handled by the router
    
    return rules

def delete_rules(db: Session, user_id: UUID) -> bool:
    """Delete rules for a user"""
    rules = get_rules_by_user_id(db, user_id)
    if not rules:
        return False
    
    db.delete(rules)
    db.commit() # Delete is a final action, can commit here or let router do it. For consistency, router should handle it.
                # However, typical delete operations often commit directly in the service.
                # For now, let's assume router handles commit for all CUD operations on rules.
                # Reverting to no commit here.
    # db.commit() 
    
    return True

def generate_organization_id() -> int:
    """Generate a random 6-digit organization ID. This will be used for User.organization_id."""
    return random.randint(100000, 999999)

def get_default_rules(role: UserRole) -> RulesCreate:
    """Get default rules based on user role. organization_id is no longer part of this.
       The organization_id for the user will be set separately.
    """
    logger.info(f"Generating default rules for role: {role}. Organization ID is handled at User level.")
    
    # Default permissions for all roles
    # organization_id is removed from RulesCreate schema
    default_rules_data = RulesCreate(
        staff_view_products=True,
        staff_edit_products=False,
        staff_view_suppliers=True,
        staff_edit_suppliers=False,
        staff_view_sales=True,
        staff_edit_sales=False,
        
        manager_view_products=True,
        manager_edit_products=True,
        manager_view_suppliers=True,
        manager_edit_suppliers=True,
        manager_view_sales=True,
        manager_edit_sales=True,
        manager_set_staff_rules=True
    )
    
    return default_rules_data 