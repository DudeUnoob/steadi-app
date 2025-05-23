from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

from app.models.enums.AlertType import AlertType

class Alert(SQLModel, table=True):
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    alert_type: AlertType = Field(index=True)
    
    # Associated records
    product_id: Optional[UUID] = Field(default=None, foreign_key="product.id", index=True)
    supplier_id: Optional[UUID] = Field(default=None, foreign_key="supplier.id", index=True)
    
    # Alert content
    message: str = Field(max_length=500)
    severity: str = Field(default="medium")  # low, medium, high, critical
    
    # Status
    is_resolved: bool = Field(default=False, index=True)
    resolved_at: Optional[datetime] = Field(default=None)
    resolved_by: Optional[UUID] = Field(default=None, foreign_key="user.id")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    created_by: Optional[UUID] = Field(default=None, foreign_key="user.id")
    
    # Relationships
    product: Optional["Product"] = Relationship(back_populates="alerts")
    supplier: Optional["Supplier"] = Relationship(back_populates="alerts")
    creator: Optional["User"] = Relationship(
        back_populates="created_alerts",
        sa_relationship_kwargs={"foreign_keys": "[Alert.created_by]"}
    )
    resolver: Optional["User"] = Relationship(
        back_populates="resolved_alerts", 
        sa_relationship_kwargs={"foreign_keys": "[Alert.resolved_by]"}
    ) 