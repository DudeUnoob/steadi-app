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
    organization_id: Optional[int] = None
    
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
    organization_id: Optional[int] = None
    
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
    
    @validator('organization_id')
    def validate_organization_id(cls, v):
        if v is not None:
            if v < 100000 or v > 999999:
                raise ValueError("Organization ID must be a 6-digit number")
        return v

class UserUpdate(SQLModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
    organization_id: Optional[int] = None
    
    @validator('email')
    def email_must_contain_at(cls, v):
        if v is not None and '@' not in v:
            raise ValueError('email must contain @')
        return v.lower() if v is not None else None
    
    @validator('organization_id')
    def validate_organization_id(cls, v):
        if v is not None:
            if v < 100000 or v > 999999:
                raise ValueError("Organization ID must be a 6-digit number")
        return v

class Token(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class SupabaseUserCreate(SQLModel):
    email: str
    supabase_id: str
    role: Optional[str] = None  # Accept role as string to match what comes from frontend
    organization_id: Optional[int] = None
    
    @validator('organization_id')
    def validate_organization_id(cls, v):
        if v is not None:
            if v < 100000 or v > 999999:
                raise ValueError("Organization ID must be a 6-digit number")
        return v
        
    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            # Normalize role to lowercase for comparison
            v = v.lower()
            # Check if role is valid
            valid_roles = [role.value for role in UserRole]
            if v not in valid_roles:
                raise ValueError(f"Invalid role: {v}. Must be one of: {', '.join(valid_roles)}")
        return v