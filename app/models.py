from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum, auto
from sqlmodel import Field, SQLModel, Relationship
from pydantic import validator

# Enums
class UserRole(str, Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    
    def __str__(self):
        return self.value

# User model
class User(SQLModel, table=True):
    """User account with authentication and authorization"""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: UserRole = Field(default=UserRole.STAFF)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships can be added as needed
    # notifications: List["Notification"] = Relationship(back_populates="user")
    
    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
            UserRole: lambda v: v.value
        }

# User schema for API responses (without password)
class UserRead(SQLModel):
    id: UUID
    email: str
    role: UserRole
    created_at: datetime
    
    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
            UserRole: lambda v: v.value
        }

# User creation schema
class UserCreate(SQLModel):
    email: str
    password: str
    role: Optional[UserRole] = UserRole.STAFF
    
    @validator('email')
    def email_must_contain_at(cls, v):
        if '@' not in v:
            raise ValueError('email must contain @')
        return v.lower()
    
    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('password must be at least 8 characters')
        return v

# Token schema
class Token(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer" 