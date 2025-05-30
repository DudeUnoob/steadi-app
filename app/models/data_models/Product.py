from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID, uuid4
from app.models.enums.AlertLevel import AlertLevel

if TYPE_CHECKING:
    from app.models.data_models.Supplier import Supplier
    from app.models.data_models.InventoryLedger import InventoryLedger
    from app.models.data_models.Sale import Sale
    from app.models.data_models.PurchaseOrderItem import PurchaseOrderItem
    from app.models.data_models.SkuAlias import SkuAlias
    from app.models.data_models.Alert import Alert

class Product(SQLModel, table=True):
    """Inventory item with stock levels and thresholds"""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    sku: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    variant: Optional[str] = None
    supplier_id: Optional[UUID] = Field(default=None, foreign_key="supplier.id")
    cost: float = Field(ge=0)
    on_hand: int = Field(default=0, ge=0)
    reorder_point: int = Field(default=0, ge=0)
    safety_stock: int = Field(default=0, ge=0)
    lead_time_days: int = Field(default=7, ge=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    alert_level: Optional[AlertLevel] = None
    user_id: UUID = Field(foreign_key="user.id")
    organization_id: Optional[int] = Field(default=None, index=True)
    
    # Relationships
    supplier: Optional["Supplier"] = Relationship(back_populates="products")
    ledger_entries: List["InventoryLedger"] = Relationship(back_populates="product")
    sales: List["Sale"] = Relationship(back_populates="product")
    purchase_order_items: List["PurchaseOrderItem"] = Relationship(back_populates="product")
    aliases: List["SkuAlias"] = Relationship(sa_relationship="SkuAlias")
    alerts: List["Alert"] = Relationship(back_populates="product") 