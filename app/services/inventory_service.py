from typing import Optional, List, Dict, Union
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import Session, select
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy import or_

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


def get_inventory(
    search: Optional[str] = None, 
    page: int = 1, 
    limit: int = 50, 
    user_id: UUID = None,
    user_ids: List[UUID] = None
) -> Dict[str, Union[List[Product], int]]:
    """
    Get paginated inventory with search.
    
    Args:
        search: Optional search text for SKU or product name
        page: Page number (1-indexed)
        limit: Number of items per page
        user_id: Single user_id for backwards compatibility
        user_ids: List of user IDs in the same organization for org-wide access
        
    Returns:
        Dictionary with items and total count
    """
    with next(get_session()) as session:
        statement = select(Product)
        
        # Apply either single user_id or multiple user_ids filter
        if user_ids:
            statement = statement.where(Product.user_id.in_(user_ids))
        elif user_id:
            statement = statement.where(Product.user_id == user_id)
            
        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                (Product.sku.ilike(search_pattern)) | (Product.name.ilike(search_pattern))
            )
        
        offset = (page - 1) * limit
        
        # Count total records with the same filters (except pagination)
        total_statement = select(Product)
        if user_ids:
            total_statement = total_statement.where(Product.user_id.in_(user_ids))
        elif user_id:
            total_statement = total_statement.where(Product.user_id == user_id)
            
        if search:
            search_pattern = f"%{search}%"
            total_statement = total_statement.where(
                (Product.sku.ilike(search_pattern)) | (Product.name.ilike(search_pattern))
            )
            
        total = len(session.execute(total_statement).scalars().all())
        
        # Apply pagination to main query
        statement = statement.offset(offset).limit(limit)
        
        results = session.execute(statement).scalars().all()
        return {"items": results, "total": total}


def get_ledger(
    product_id: UUID, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None, 
    user_id: UUID = None,
    user_ids: List[UUID] = None
) -> List[InventoryLedger]:
    """
    Get inventory audit trail for a product.
    
    Args:
        product_id: ID of the product to get ledger for
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        user_id: Single user_id for backwards compatibility
        user_ids: List of user IDs in the same organization for org-wide access
        
    Returns:
        List of inventory ledger entries
    """
    with next(get_session()) as session:
        # Check product exists and belongs to user/organization
        if user_ids:
            product = session.execute(select(Product).where(
                (Product.id == product_id) & (Product.user_id.in_(user_ids))
            )).scalar_one_or_none()
        elif user_id:
            product = session.execute(select(Product).where(
                (Product.id == product_id) & (Product.user_id == user_id)
            )).scalar_one_or_none()
        else:
            product = session.execute(select(Product).where(
                Product.id == product_id
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