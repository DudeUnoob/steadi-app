from app.models.data_models.Product import Product
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class Sale(SQLModel, table=True):
    """Record of product sales for analytics"""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    product_id: UUID = Field(foreign_key="product.id", index=True)
    quantity: int = Field(gt=0)
    sale_date: datetime = Field(default_factory=datetime.utcnow, index=True)
    # Relationships
    product: Product = Relationship(back_populates="sales")
