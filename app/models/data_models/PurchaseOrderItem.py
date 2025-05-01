from app.models.data_models.Product import Product
from app.models.data_models.PurchaseOrder import PurchaseOrder
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class PurchaseOrderItem(SQLModel, table=True):
    """Line item in a purchase order"""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    po_id: UUID = Field(foreign_key="purchaseorder.id")
    product_id: UUID = Field(foreign_key="product.id")
    quantity: int = Field(gt=0)
    unit_cost: float = Field(ge=0)
    # Relationships
    purchase_order: PurchaseOrder = Relationship(back_populates="items")
    product: Product = Relationship(back_populates="purchase_order_items")
