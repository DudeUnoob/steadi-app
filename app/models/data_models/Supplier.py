from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from app.models.data_models.Product import Product
    from app.models.data_models.PurchaseOrder import PurchaseOrder
    from app.models.data_models.Alert import Alert

class Supplier(SQLModel, table=True):
    """Supplier or vendor information"""
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    contact_email: str
    phone: Optional[str] = None
    lead_time_days: int = Field(default=7)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: UUID = Field(foreign_key="user.id")
    organization_id: Optional[int] = Field(default=None, index=True)
    
    # Relationships
    products: List["Product"] = Relationship(back_populates="supplier")
    purchase_orders: List["PurchaseOrder"] = Relationship(back_populates="supplier")
    alerts: List["Alert"] = Relationship(back_populates="supplier") 