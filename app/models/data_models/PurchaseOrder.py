from app.models.enums.POStatus import POStatus
from app.models.data_models.PurchaseOrderItem import PurchaseOrderItem
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List

class PurchaseOrder(SQLModel, table=True):
    """Order to suppliers for inventory replenishment"""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    supplier_id: UUID = Field(foreign_key="supplier.id", index=True)
    status: POStatus = Field(default=POStatus.DRAFT, index=True)
    created_by: UUID = Field(foreign_key="user.id")
    pdf_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Relationships
    supplier: "Supplier" = Relationship(back_populates="purchase_orders")
    items: List["PurchaseOrderItem"] = Relationship(back_populates="purchase_order")
