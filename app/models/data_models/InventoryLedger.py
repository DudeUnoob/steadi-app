from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from app.models.data_models.Product import Product

class InventoryLedger(SQLModel, table=True):
    """Audit trail for all inventory changes"""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    product_id: UUID = Field(foreign_key="product.id")
    quantity_delta: int
    quantity_after: int
    source: str = Field(index=True)  # shopify, square, lightspeed, csv, po_receive, manual
    reference_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
   
    product: "Product" = Relationship(back_populates="ledger_entries")
