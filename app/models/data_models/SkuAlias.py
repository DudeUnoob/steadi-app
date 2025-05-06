from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from app.models.data_models.Product import Product

class SkuAlias(SQLModel, table=True):
    """Alias or alternative SKU for a product"""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    alias_sku: str = Field(index=True)
    canonical_sku: str = Field(foreign_key="product.sku")
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: UUID = Field(foreign_key="user.id")
    
    # Use string for the relationship target to avoid circular imports
    product: "Product" = Relationship(sa_relationship="Product") 