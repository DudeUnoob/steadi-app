from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional, List
from uuid import UUID, uuid4
import logging

from app.services.inventory_service import update_inventory, get_inventory, get_ledger
from app.schemas.inventory import ProductCreate, ProductUpdate, ProductOut, InventoryResponse, InventoryLedgerOut
from app.models.data_models.Product import Product
from app.models.data_models.Supplier import Supplier
from app.db.database import get_db
from sqlmodel import Session, select
from app.api.mvp.auth import get_current_user
from app.api.auth.supabase import get_current_supabase_user
from app.models.data_models.User import User
from app.models.enums.UserRole import UserRole

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api', tags=['inventory'])

# Combined authentication dependency
async def get_authenticated_user(
    request: Request,
    token_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Combined authentication that works with both JWT tokens and Supabase tokens.
    First tries traditional JWT auth, and if that fails, tries Supabase auth.
    Returns the authenticated user or raises an authentication error.
    """
    # If traditional JWT auth worked, use that user
    if token_user:
        logger.info(f"User authenticated via JWT: {token_user.email}")
        return token_user
    
    try:
        # Try Supabase auth if JWT fails
        supabase_user = await get_current_supabase_user(request)
        supabase_id = supabase_user.get("id")
        
        if not supabase_id:
            logger.error("Supabase user has no ID")
            raise HTTPException(status_code=401, detail="Invalid Supabase user information")
        
        # Find user by Supabase ID
        user = db.exec(select(User).where(User.supabase_id == supabase_id)).first()
        
        if not user:
            # This shouldn't happen if the sync endpoint is working properly
            logger.error(f"No user found for Supabase ID: {supabase_id}")
            raise HTTPException(status_code=401, detail="User not found in system")
        
        logger.info(f"User authenticated via Supabase: {user.email}")
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Not authenticated")

# Combined authentication for manager operations
async def get_authenticated_manager(
    request: Request,
    token_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Combined authentication with role check for manager/owner operations.
    """
    user = await get_authenticated_user(request, token_user, db)
    
    if user.role not in [UserRole.OWNER, UserRole.MANAGER]:
        logger.error(f"User {user.email} has insufficient permissions: {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return user

@router.post('/inventory', response_model=ProductOut)
async def create_product(
    request: Request,
    product: ProductCreate, 
    session: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_manager)
):
    """Create a new product in the inventory"""
    existing_product = session.execute(
        select(Product).where(
            (Product.sku == product.sku) & 
            (Product.user_id == current_user.id)
        )
    ).scalar_one_or_none()
    
    if existing_product:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Product with SKU {product.sku} already exists")
    
    supplier = session.get(Supplier, product.supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid supplier_id: Supplier with ID {product.supplier_id} not found.")
    
    db_product = Product(
        id=uuid4(),
        user_id=current_user.id,
        sku=product.sku,
        name=product.name,
        variant=product.variant,
        supplier_id=product.supplier_id,
        cost=product.cost,
        on_hand=product.on_hand,
        reorder_point=product.reorder_point,
        safety_stock=product.safety_stock,
        lead_time_days=product.lead_time_days
    )
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@router.get('/inventory', response_model=InventoryResponse)
async def read_inventory(
    request: Request,
    search: Optional[str] = None, 
    page: int = 1, 
    limit: int = 50,
    current_user: User = Depends(get_authenticated_user)
):
    """Get paginated inventory with optional search"""
    return get_inventory(search, page, limit, user_id=current_user.id)

@router.get('/inventory/{sku}', response_model=ProductOut)
async def read_product(
    request: Request,
    sku: str, 
    session: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    """Get a specific product by SKU"""
    statement = select(Product).where(
        (Product.sku == sku) & 
        (Product.user_id == current_user.id)
    )
    result = session.exec(statement)
    product = result.first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.patch('/inventory/{sku}', response_model=ProductOut)
async def update_product(
    request: Request,
    sku: str, 
    product_update: ProductUpdate, 
    session: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_manager)
):
    """Update product inventory details"""
    statement = select(Product).where(
        (Product.sku == sku) & 
        (Product.user_id == current_user.id)
    )
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
async def adjust_inventory(
    request: Request,
    sku: str, 
    quantity_delta: int, 
    source: str = 'manual', 
    reference_id: Optional[str] = None,
    current_user: User = Depends(get_authenticated_manager)
):
    """Adjust inventory quantity with audit trail"""
    try:
        return update_inventory(
            sku, 
            quantity_delta, 
            source, 
            reference_id, 
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/inventory/ledger/{product_id}', response_model=List[InventoryLedgerOut])
async def read_ledger(
    request: Request,
    product_id: UUID, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    current_user: User = Depends(get_authenticated_user)
):
    """Get inventory audit trail for a product"""
    from datetime import datetime
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    # Only return ledger entries for products owned by the current user
    return get_ledger(product_id, start, end, user_id=current_user.id) 