from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from uuid import UUID
import datetime

class Permission(SQLModel, table=True):
    """Model for defining available permissions in the system"""
    __tablename__ = "rules"

    id: str = Field(primary_key=True)
    name: str = Field(...)
    description: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: Optional[datetime.datetime] = Field(default=None)
    
    # Relationships
    role_permissions: List["RolePermission"] = Relationship(back_populates="permission")


class RolePermission(SQLModel, table=True):
    """Model for associating roles with permissions for each organization"""
    __tablename__ = "role_permission"

    id: UUID = Field(primary_key=True)
    organization_id: str = Field(...)
    role: str = Field(...)  # 'owner', 'manager', 'staff'
    permission_id: str = Field(foreign_key="rules.id")
    enabled: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    
    # Relationships
    permission: Permission = Relationship(back_populates="role_permissions") 