from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from uuid import UUID, uuid4

from app.services.inventory_service import update_inventory, get_inventory, get_ledger
from app.schemas.inventory import ProductCreate, ProductUpdate, ProductOut, InventoryResponse, InventoryLedgerOut
from app.models.data_models.Product import Product
from app.models.data_models.Supplier import Supplier
from app.db.database import get_db
from sqlmodel import Session, select

router = APIRouter(prefix='/api', tags=['inventory'])

@router.post('/inventory', response_model=ProductOut)
async def create_product(product: ProductCreate, session: Session = Depends(get_db)):
    """Create a new product in the inventory"""
    existing_product = session.execute(select(Product).where(Product.sku == product.sku)).scalar_one_or_none()
    if existing_product:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Product with SKU {product.sku} already exists")
    
    supplier = session.get(Supplier, product.supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid supplier_id: Supplier with ID {product.supplier_id} not found.")
    
    db_product = Product.from_orm(product)
    db_product.id = uuid4()
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@router.get('/inventory', response_model=InventoryResponse)
async def read_inventory(search: Optional[str] = None, page: int = 1, limit: int = 50):
    """Get paginated inventory with optional search"""
    return get_inventory(search, page, limit)

@router.get('/inventory/{sku}', response_model=ProductOut)
async def read_product(sku: str, session: Session = Depends(get_db)):
    """Get a specific product by SKU"""
    statement = select(Product).where(Product.sku == sku)
    result = session.exec(statement)
    product = result.first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.patch('/inventory/{sku}', response_model=ProductOut)
async def update_product(sku: str, product_update: ProductUpdate, session: Session = Depends(get_db)):
    """Update product inventory details"""
    statement = select(Product).where(Product.sku == sku)
    result = session.exec(statement)
    db_product = result.first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_product, key, value)
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@router.post('/inventory/{sku}/adjust', response_model=ProductOut)
async def adjust_inventory(sku: str, quantity_delta: int, source: str = 'manual', reference_id: Optional[str] = None):
    """Adjust inventory quantity with audit trail"""
    try:
        return update_inventory(sku, quantity_delta, source, reference_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/inventory/ledger/{product_id}', response_model=List[InventoryLedgerOut])
async def read_ledger(product_id: UUID, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get inventory audit trail for a product"""
    from datetime import datetime
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    return get_ledger(product_id, start, end) 