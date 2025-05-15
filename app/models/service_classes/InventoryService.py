from typing import Dict, List, Optional, Union
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select, func
from app.models.data_models.Product import Product
from app.models.data_models.InventoryLedger import InventoryLedger

class InventoryService:
    """Manages inventory operations and ledger entries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_inventory(self, sku: str, quantity_delta: int, source: str, reference_id: Optional[str] = None, user_id: UUID = None) -> Product:
        """Update inventory levels with audit trail"""
        # Find the product, filtered by user_id if provided
        query = select(Product).where(Product.sku == sku)
        if user_id:
            query = query.where(Product.user_id == user_id)
            
        product = self.db.exec(query).first()
        if not product:
            raise ValueError(f"Product with SKU {sku} not found or you don't have permission to access it")
        
        # Calculate new quantity
        new_quantity = max(0, product.on_hand + quantity_delta)
        
        # Create ledger entry
        ledger_entry = InventoryLedger(
            product_id=product.id,
            quantity_delta=quantity_delta,
            quantity_after=new_quantity,
            source=source,
            reference_id=reference_id,
            user_id=product.user_id  # Ensure ledger entry has the user_id
        )
        
        # Update product inventory
        product.on_hand = new_quantity
        
        # Save changes
        self.db.add(ledger_entry)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def get_inventory(self, search: Optional[str] = None, page: int = 1, limit: int = 50, user_id: UUID = None) -> Dict[str, Union[List[Product], int]]:
        """Get paginated inventory with search"""
        query = select(Product)
        
        # Apply user filter if provided
        if user_id:
            query = query.where(Product.user_id == user_id)
        
        # Apply search filter if provided
        if search:
            query = query.filter(
                (Product.sku.ilike(f"%{search}%")) | 
                (Product.name.ilike(f"%{search}%"))
            )
        
        # Count total items
        count_query = select(func.count()).select_from(Product)
        if user_id:
            count_query = count_query.where(Product.user_id == user_id)
            
        if search:
            count_query = count_query.where(
                (Product.sku.ilike(f"%{search}%")) | 
                (Product.name.ilike(f"%{search}%"))
            )
        total = self.db.exec(count_query).one()
        
        # Calculate pagination
        skip = (page - 1) * limit
        products = self.db.exec(query.offset(skip).limit(limit)).all()
        
        return {
            "items": products,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    def get_ledger(self, product_id: UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, user_id: UUID = None) -> List[InventoryLedger]:
        """Get inventory audit trail for a product"""
        # First verify the product belongs to the user if user_id provided
        if user_id:
            product = self.db.exec(select(Product).where(
                (Product.id == product_id) &
                (Product.user_id == user_id)
            )).first()
            
            if not product:
                return []  # Return empty list if product not found or not owned by user
        
        query = select(InventoryLedger).where(InventoryLedger.product_id == product_id)
        
        # Apply user filter if provided
        if user_id:
            query = query.where(InventoryLedger.user_id == user_id)
        
        # Apply date filters if provided
        if start_date:
            query = query.where(InventoryLedger.timestamp >= start_date)
        if end_date:
            query = query.where(InventoryLedger.timestamp <= end_date)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(InventoryLedger.timestamp.desc())
        
        return self.db.exec(query).all()
