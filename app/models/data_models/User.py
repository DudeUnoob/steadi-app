from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID
from app.models.enums.UserRole import UserRole
from app.models.data_models.Notification import Notification

class User(SQLModel, table=True):
    """User account with authentication and authorization"""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: UserRole = Field(default=UserRole.STAFF)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Relationships
    notifications: List["Notification"] = Relationship(back_populates="user")
