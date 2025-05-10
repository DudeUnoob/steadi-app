from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum, auto
from sqlmodel import Field, SQLModel, Relationship
from pydantic import validator
from app.models.enums.UserRole import UserRole

class UserRead(SQLModel):
    id: UUID
    email: str
    role: UserRole
    created_at: datetime
    supabase_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
            UserRole: lambda v: v.value
        }

class UserCreate(SQLModel):
    email: str
    password: Optional[str] = None
    role: Optional[UserRole] = UserRole.STAFF
    supabase_id: Optional[str] = None
    
    @validator('email')
    def email_must_contain_at(cls, v):
        if '@' not in v:
            raise ValueError('email must contain @')
        return v.lower()
    
    @validator('password')
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('password must be at least 8 characters')
        return v

class Token(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class SupabaseUserCreate(SQLModel):
    email: str
    supabase_id: str
    role: Optional[UserRole] = UserRole.STAFF