from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from app.models.data_models.Product import Product

class Sale(SQLModel, table=True):
    """Sale record representing inventory transactions"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    product_id: UUID = Field(foreign_key="product.id")
    quantity: int = 1
    sale_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    user_id: UUID = Field(foreign_key="user.id")
    organization_id: Optional[int] = Field(default=None, nullable=True, index=True)
    
    
    product: "Product" = Relationship(back_populates="sales")
