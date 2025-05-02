from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum, auto
from sqlmodel import Field, SQLModel, Relationship
from pydantic import validator
from app.models.enums.UserRole import UserRole
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