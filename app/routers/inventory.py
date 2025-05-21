from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
import logging

from app.services.inventory_service import update_inventory, get_inventory, get_ledger
from app.schemas.inventory import ProductCreate, ProductUpdate, ProductOut, InventoryResponse, InventoryLedgerOut
from app.models.data_models.Product import Product
from app.models.data_models.Supplier import Supplier
from app.db.database import get_db
from sqlmodel import Session, select
from app.api.mvp.auth import get_current_user, check_org_membership_and_permissions
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

# Helper function for organization permissions
def get_org_user_with_permissions(operation_type: str):
    """
    Create a dependency function that checks organization membership and permissions.
    This avoids the need for lambdas with request parameter references.
    
    Args:
        operation_type: The operation type to check permissions for (e.g. "view_products")
        
    Returns:
        A dependency function that gets the user with verified permissions
    """
    def dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> User:
        return check_org_membership_and_permissions(
            current_user=current_user,
            operation_type=operation_type,
            db=db
        )
    return dependency

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
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("view_products"))
):
    """Get paginated inventory with optional search by organization"""
    # Get all products for the user's organization instead of just the user
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an organization"
        )
    
    # Get all users in the organization to find their products
    users_in_org = session.exec(
        select(User).where(User.organization_id == current_user.organization_id)
    ).all()
    
    user_ids = [user.id for user in users_in_org]
    logger.info(f"Fetching inventory for organization {current_user.organization_id} with {len(user_ids)} users")
    
    return get_inventory(search, page, limit, user_ids=user_ids)

@router.get('/inventory/{sku}', response_model=ProductOut)
async def read_product(
    request: Request,
    sku: str, 
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("view_products"))
):
    """Get a specific product by SKU within organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an organization"
        )
    
    # Get all users in the organization
    users_in_org = session.exec(
        select(User).where(User.organization_id == current_user.organization_id)
    ).all()
    
    user_ids = [user.id for user in users_in_org]
    
    # Find product belonging to any user in the organization
    statement = select(Product).where(
        (Product.sku == sku) & 
        (Product.user_id.in_(user_ids))
    )
    result = session.exec(statement)
    product = result.first()
    
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found in your organization")
    return product

@router.patch('/inventory/{sku}', response_model=ProductOut)
async def update_product(
    request: Request,
    sku: str, 
    product_update: ProductUpdate, 
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("edit_products"))
):
    """Update product inventory details within organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an organization"
        )
    
    # Get all users in the organization
    users_in_org = session.exec(
        select(User).where(User.organization_id == current_user.organization_id)
    ).all()
    
    user_ids = [user.id for user in users_in_org]
    
    # Find product belonging to any user in the organization
    statement = select(Product).where(
        (Product.sku == sku) & 
        (Product.user_id.in_(user_ids))
    )
    result = session.exec(statement)
    db_product = result.first()
    
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found in your organization")
    
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
    current_user: User = Depends(get_org_user_with_permissions("edit_products"))
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
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("view_products"))
):
    """Get inventory ledger history for a product within the organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an organization"
        )
    
    # Get all users in the organization
    users_in_org = session.exec(
        select(User).where(User.organization_id == current_user.organization_id)
    ).all()
    
    user_ids = [user.id for user in users_in_org]
    logger.info(f"Fetching ledger for product {product_id} for organization {current_user.organization_id}")
    
    start_datetime = None
    if start_date:
        start_datetime = datetime.fromisoformat(start_date)
    
    end_datetime = None
    if end_date:
        end_datetime = datetime.fromisoformat(end_date)
    
    return get_ledger(
        product_id=product_id,
        start_date=start_datetime,
        end_date=end_datetime,
        user_ids=user_ids
    ) 