from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID

class Supplier(SQLModel, table=True):
    """Supplier or vendor information"""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    contact_email: str
    phone: Optional[str] = None
    lead_time_days: int = Field(default=7)
    # Relationships
    products: List["Product"] = Relationship(back_populates="supplier")
    purchase_orders: List["PurchaseOrder"] = Relationship(back_populates="supplier")

