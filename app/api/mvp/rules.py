from typing import Optional, List
from sqlmodel import Session, select
from app.models.data_models.Rules import Rules
from app.models.data_models.User import User
from app.schemas.data_models.Rules import RulesCreate, RulesUpdate
from app.models.enums.UserRole import UserRole
import random
import logging

logger = logging.getLogger(__name__)

def get_rules_by_organization_id(db: Session, organization_id: int) -> Optional[Rules]:
    """Get rules for a specific organization"""
    return db.exec(select(Rules).where(Rules.organization_id == organization_id)).first()

def create_rules(db: Session, organization_id: int, rules_data: RulesCreate) -> Rules:
    """Create new rules for an organization. Assumes rules do not already exist."""
    # We no longer fetch a user here to create rules, rules are directly tied to an organization_id
    # user = db.exec(select(User).where(User.id == user_id)).first()
    # if not user:
    #     raise ValueError(f"User with ID {user_id} not found for creating rules")
    
    # Check if rules for this organization_id already exist
    existing_rules = get_rules_by_organization_id(db, organization_id)
    if existing_rules:
        # This scenario should ideally be handled by the calling router/service
        # For now, let's raise an error or return existing. Raising error is cleaner.
        raise ValueError(f"Rules for organization ID {organization_id} already exist.")

    rules = Rules(organization_id=organization_id, **rules_data.dict(exclude_unset=True))
    
    db.add(rules)
    # db.commit() and db.refresh() are typically handled by the router
    
    return rules

def update_rules(db: Session, organization_id: int, rules_data: RulesUpdate) -> Optional[Rules]:
    """Update existing rules for an organization"""
    rules = get_rules_by_organization_id(db, organization_id)
    if not rules:
        return None
    
    # Only update fields that are not None in the update payload
    rules_dict = rules_data.dict(exclude_unset=True, exclude_none=True)
    
    # Only update fields that are provided in the update
    for key, value in rules_dict.items():
        setattr(rules, key, value)
    
    db.add(rules)
    
    return rules

def delete_rules(db: Session, organization_id: int) -> bool:
    """Delete rules for an organization"""
    rules = get_rules_by_organization_id(db, organization_id)
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
    """Get default rules based on user role.
       The organization_id for the User/Rules will be set separately when creating/assigning rules.
    """
    logger.info(f"Generating default rules for role: {role}. Organization ID is handled at User/Rules level.")
    
    # Default permissions for all roles
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