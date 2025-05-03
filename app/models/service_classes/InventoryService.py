from typing import Dict, List, Optional, Union
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select
from app.models.data_models.Product import Product
from app.models.data_models.InventoryLedger import InventoryLedger

class InventoryService:
    """Manages inventory operations and ledger entries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_inventory(self, sku: str, quantity_delta: int, source: str, reference_id: Optional[str] = None) -> Product:
        """Update inventory levels with audit trail"""
        # Get product
        product = self.db.exec(select(Product).where(Product.sku == sku)).first()
        if not product:
            raise ValueError(f"Product with SKU {sku} not found")
        
        # Update quantity
        new_quantity = product.on_hand + quantity_delta
        if new_quantity < 0:
            raise ValueError("Insufficient stock")
        
        # Create ledger entry
        ledger_entry = InventoryLedger(
            product_id=product.id,
            quantity_delta=quantity_delta,
            quantity_after=new_quantity,
            source=source,
            reference_id=reference_id
        )
        
        # Update product
        product.on_hand = new_quantity
        
        # Save changes
        self.db.add(ledger_entry)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def get_inventory(self, search: Optional[str] = None, page: int = 1, limit: int = 50) -> Dict[str, Union[List[Product], int]]:
        """Get paginated inventory with search"""
        query = select(Product)
        
        if search:
            query = query.filter(
                (Product.sku.ilike(f"%{search}%")) | 
                (Product.name.ilike(f"%{search}%"))
            )
        
        # Calculate pagination
        skip = (page - 1) * limit
        total = self.db.exec(query.count()).first()
        products = self.db.exec(query.offset(skip).limit(limit)).all()
        
        return {
            "items": products,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    def get_ledger(self, product_id: UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[InventoryLedger]:
        """Get inventory audit trail for a product"""
        query = select(InventoryLedger).where(InventoryLedger.product_id == product_id)
        
        if start_date:
            query = query.where(InventoryLedger.timestamp >= start_date)
        if end_date:
            query = query.where(InventoryLedger.timestamp <= end_date)
            
        query = query.order_by(InventoryLedger.timestamp.desc())
        
        return self.db.exec(query).all()
