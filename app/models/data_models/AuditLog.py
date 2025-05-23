from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from app.models.enums.AuditAction import AuditAction

class AuditLog(SQLModel, table=True):
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # User who performed the action
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id", index=True)
    
    # Action details
    action: AuditAction = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Request context
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 support
    user_agent: Optional[str] = Field(default=None, max_length=500)
    
    # Resource information
    resource_type: Optional[str] = Field(default=None, max_length=100, index=True)
    resource_id: Optional[str] = Field(default=None, max_length=100, index=True)
    
    # Detailed action data (JSON)
    details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Outcome
    success: bool = Field(default=True, index=True)
    error_message: Optional[str] = Field(default=None, max_length=1000)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="audit_logs")
    
    class Config:
        arbitrary_types_allowed = True 