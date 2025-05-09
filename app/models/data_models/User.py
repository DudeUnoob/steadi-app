from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID, uuid4
from app.models.enums.UserRole import UserRole

if TYPE_CHECKING:
    from app.models.data_models.Notification import Notification

class User(SQLModel, table=True):
    """User account with authentication and authorization"""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: Optional[str] = None
    supabase_id: Optional[str] = Field(default=None, unique=True, index=True)
    role: UserRole = Field(default=UserRole.STAFF)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Relationships
    notifications: List["Notification"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
            UserRole: lambda v: v.value
        }