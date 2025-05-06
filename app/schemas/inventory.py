from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ProductBase(BaseModel):
    sku: str
    name: str
    variant: Optional[str] = None
    supplier_id: UUID
    cost: float = Field(ge=0)
    on_hand: int = Field(default=0, ge=0)
    reorder_point: int = Field(default=0, ge=0)
    safety_stock: int = Field(default=0, ge=0)
    lead_time_days: int = Field(default=7, ge=1)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    on_hand: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    safety_stock: Optional[int] = Field(None, ge=0)

class ProductOut(ProductBase):
    id: UUID
    alert_level: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class InventoryLedgerOut(BaseModel):
    id: UUID
    product_id: UUID
    quantity_delta: int
    quantity_after: int
    source: str
    reference_id: Optional[str]
    timestamp: datetime
    
    class Config:
        orm_mode = True

class InventoryResponse(BaseModel):
    items: List[ProductOut]
    total: int 