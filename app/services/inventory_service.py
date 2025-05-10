from typing import Optional, List, Dict, Union
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import Session, select
from sqlalchemy.orm import Session as SQLAlchemySession

from app.models.data_models.Product import Product
from app.models.data_models.InventoryLedger import InventoryLedger

from app.db.database import get_db, engine


def get_session():
    """Create a session for direct use in service functions"""
    session = SQLAlchemySession(engine)
    try:
        yield session
    finally:
        session.close()


def update_inventory(sku: str, quantity_delta: int, source: str, reference_id: Optional[str] = None, user_id: UUID = None) -> Product:
    """Update inventory levels with audit trail"""
    with next(get_session()) as session:
        statement = select(Product).where(Product.sku == sku)
        
        if user_id:
            statement = statement.where(Product.user_id == user_id)
            
        result = session.execute(statement)
        product = result.scalar_one_or_none()
        
        if not product:
            raise ValueError(f"Product with SKU {sku} not found")
        
        new_quantity = product.on_hand + quantity_delta
        if new_quantity < 0:
            raise ValueError(f"Inventory for SKU {sku} cannot be negative")
        product.on_hand = new_quantity
        
        ledger_entry = InventoryLedger(
            id=uuid4(),
            product_id=product.id,
            quantity_delta=quantity_delta,
            quantity_after=new_quantity,
            source=source,
            reference_id=reference_id
        )
        session.add(ledger_entry)
        session.add(product)
        session.commit()
        session.refresh(product)
        return product


def get_inventory(search: Optional[str] = None, page: int = 1, limit: int = 50, user_id: UUID = None) -> Dict[str, Union[List[Product], int]]:
    """Get paginated inventory with search"""
    with next(get_session()) as session:
        statement = select(Product)
        
        if user_id:
            statement = statement.where(Product.user_id == user_id)
            
        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                (Product.sku.ilike(search_pattern)) | (Product.name.ilike(search_pattern))
            )
        
        offset = (page - 1) * limit
        
        total_statement = select(Product)
        if user_id:
            total_statement = total_statement.where(Product.user_id == user_id)
            
        total = len(session.execute(total_statement).scalars().all())
        statement = statement.offset(offset).limit(limit)
        
        results = session.execute(statement).scalars().all()
        return {"items": results, "total": total}


def get_ledger(product_id: UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, user_id: UUID = None) -> List[InventoryLedger]:
    """Get inventory audit trail for a product"""
    with next(get_session()) as session:
        if user_id:
            product = session.execute(select(Product).where(
                (Product.id == product_id) & (Product.user_id == user_id)
            )).scalar_one_or_none()
            
            if not product:
                return []
        
        statement = select(InventoryLedger).where(InventoryLedger.product_id == product_id)
        if start_date:
            statement = statement.where(InventoryLedger.timestamp >= start_date)
        if end_date:
            statement = statement.where(InventoryLedger.timestamp <= end_date)
        
        results = session.execute(statement).scalars().all()
        return results 