from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from uuid import UUID
import logging
import random

from app.models.data_models.User import User
from app.models.enums.UserRole import UserRole

logger = logging.getLogger(__name__)

class OrganizationService:
    """Service for managing organization-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_organization_id(self) -> int:
        """Generate a random 6-digit organization ID"""
        return random.randint(100000, 999999)
    
    def get_organization_users(self, organization_id: int) -> List[User]:
        """Get all users in an organization"""
        try:
            users = self.db.exec(select(User).where(
                User.organization_id == organization_id
            )).all()
            return users
        except Exception as e:
            logger.error(f"Error getting organization users: {str(e)}")
            return {"error": str(e)}
    
    def add_user_to_organization(self, user_id: UUID, organization_id: int) -> User:
        """Add a user to an organization"""
        try:
            user = self.db.exec(select(User).where(
                User.id == user_id
            )).first()
            
            if not user:
                return {"error": "User not found"}
            
            # Check if organization exists by finding at least one user with this org ID
            org_exists = self.db.exec(select(User).where(
                User.organization_id == organization_id
            )).first()
            
            if not org_exists:
                return {"error": "Organization not found"}
            
            user.organization_id = organization_id
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Added user {user.id} to organization {organization_id}")
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding user to organization: {str(e)}")
            return {"error": str(e)}
    
    def remove_user_from_organization(self, user_id: UUID, organization_id: int) -> Dict[str, str]:
        """Remove a user from an organization"""
        try:
            user = self.db.exec(select(User).where(
                (User.id == user_id) &
                (User.organization_id == organization_id)
            )).first()
            
            if not user:
                return {"error": "User not found in this organization"}
            
            # Cannot remove an OWNER from their organization
            if user.role == UserRole.OWNER:
                return {"error": "Cannot remove an owner from their organization"}
            
            user.organization_id = None
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Removed user {user.id} from organization {organization_id}")
            return {"message": "User removed from organization successfully"}
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing user from organization: {str(e)}")
            return {"error": str(e)}
    
    def change_user_role(self, user_id: UUID, organization_id: int, new_role: UserRole) -> User:
        """Change a user's role within an organization"""
        try:
            user = self.db.exec(select(User).where(
                (User.id == user_id) &
                (User.organization_id == organization_id)
            )).first()
            
            if not user:
                return {"error": "User not found in this organization"}
            
            # Cannot have multiple owners in an organization
            if new_role == UserRole.OWNER:
                existing_owner = self.db.exec(select(User).where(
                    (User.organization_id == organization_id) &
                    (User.role == UserRole.OWNER) &
                    (User.id != user_id)
                )).first()
                
                if existing_owner:
                    return {"error": "Organization already has an owner"}
            
            user.role = new_role
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Changed user {user.id} role to {new_role} in organization {organization_id}")
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error changing user role: {str(e)}")
            return {"error": str(e)} 