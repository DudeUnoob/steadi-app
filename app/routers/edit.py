from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
import logging

from app.db.database import get_db
from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.data_models.Supplier import Supplier
from app.models.service_classes.EditService import EditService
from app.api.mvp.edit_service import MVPEditService
from app.models.data_models.User import User
from app.api.auth.supabase import get_current_supabase_user
from app.api.mvp.auth import get_current_user, get_manager_user
from app.api.permissions import (
    require_view_products, require_edit_products,
    require_view_suppliers, require_edit_suppliers,
    require_view_sales, require_edit_sales
)


EditServiceClass = MVPEditService
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/edit", tags=["edit"])

# Add a new model that includes product count
class SupplierWithProductCount(BaseModel):
    id: UUID
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    lead_time_days: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    product_count: int

    class Config:
        orm_mode = True

class ProductCreate(BaseModel):
    sku: str
    name: str
    supplier_id: UUID
    cost: float
    on_hand: int
    reorder_point: int
    safety_stock: Optional[int] = None
    lead_time_days: Optional[int] = None

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    supplier_id: Optional[UUID] = None
    cost: Optional[float] = None
    on_hand: Optional[int] = None
    reorder_point: Optional[int] = None
    safety_stock: Optional[int] = None
    lead_time_days: Optional[int] = None

class SupplierCreate(BaseModel):
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    lead_time_days: int = 7
    notes: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    lead_time_days: int = 7
    notes: Optional[str] = None

class SaleCreate(BaseModel):
    product_id: UUID
    quantity: int
    sale_date: Optional[datetime] = None
    notes: Optional[str] = None

class SaleUpdate(BaseModel):
    quantity: Optional[int] = None
    sale_date: Optional[datetime] = None
    notes: Optional[str] = None

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
    
    from app.models.enums.UserRole import UserRole
    if user.role not in [UserRole.OWNER, UserRole.MANAGER]:
        logger.error(f"User {user.email} has insufficient permissions: {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return user

# Product endpoints
@router.get("/products", response_model=List[Product], dependencies=[Depends(require_view_products())])
async def list_products(
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get all products for the current user's organization"""
    edit_service = EditServiceClass(db)
    return edit_service.get_products(current_user.id, current_user.organization_id)

@router.post("/products", status_code=status.HTTP_201_CREATED, response_model=Product, dependencies=[Depends(require_edit_products())])
async def create_product(
    request: Request,
    product_data: ProductCreate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Create a new product (requires edit_products permission)"""
    edit_service = EditServiceClass(db)
    result = edit_service.create_product(product_data.dict(), current_user.id, current_user.organization_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.put("/products/{product_id}", response_model=Product, dependencies=[Depends(require_edit_products())])
async def update_product(
    request: Request,
    product_id: UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Update a product (requires edit_products permission)"""
    edit_service = EditServiceClass(db)
    result = edit_service.update_product(
        product_id, 
        product_data.dict(exclude_unset=True),
        current_user.id,
        current_user.organization_id
    )
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.delete("/products/{product_id}", response_model=Dict[str, str], dependencies=[Depends(require_edit_products())])
async def delete_product(
    request: Request,
    product_id: UUID,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Delete a product (requires edit_products permission)"""
    edit_service = EditServiceClass(db)
    result = edit_service.delete_product(product_id, current_user.id, current_user.organization_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

# Supplier endpoints
@router.get("/suppliers", response_model=List[SupplierWithProductCount], dependencies=[Depends(require_view_suppliers())])
async def list_suppliers(
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get all suppliers for the current user with product counts (requires view_suppliers permission)"""
    edit_service = EditServiceClass(db)
    return edit_service.get_suppliers(current_user.id, current_user.organization_id)

@router.post("/suppliers", status_code=status.HTTP_201_CREATED, response_model=Supplier, dependencies=[Depends(require_edit_suppliers())])
async def create_supplier(
    request: Request,
    supplier_data: SupplierCreate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Create a new supplier (requires edit_suppliers permission)"""
    edit_service = EditServiceClass(db)
    result = edit_service.create_supplier(supplier_data.dict(), current_user.id, current_user.organization_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.put("/suppliers/{supplier_id}", response_model=Supplier, dependencies=[Depends(require_edit_suppliers())])
async def update_supplier(
    request: Request,
    supplier_id: UUID,
    supplier_data: SupplierUpdate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Update a supplier (requires edit_suppliers permission)"""
    edit_service = EditServiceClass(db)
    result = edit_service.update_supplier(
        supplier_id, 
        supplier_data.dict(exclude_unset=True),
        current_user.id,
        current_user.organization_id
    )
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.delete("/suppliers/{supplier_id}", response_model=Dict[str, str], dependencies=[Depends(require_edit_suppliers())])
async def delete_supplier(
    request: Request,
    supplier_id: UUID,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Delete a supplier (requires edit_suppliers permission)"""
    edit_service = EditServiceClass(db)
    result = edit_service.delete_supplier(supplier_id, current_user.id, current_user.organization_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

# Sale endpoints
@router.get("/sales", response_model=List[Sale], dependencies=[Depends(require_view_sales())])
async def list_sales(
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get all sales for the current user or organization (requires view_sales permission)"""
    edit_service = EditServiceClass(db)
    return edit_service.get_sales(current_user.id, current_user.organization_id)

@router.post("/sales", status_code=status.HTTP_201_CREATED, response_model=Sale, dependencies=[Depends(require_edit_sales())])
async def create_sale(
    request: Request,
    sale_data: SaleCreate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Create a new sale record (requires edit_sales permission)"""
    edit_service = EditServiceClass(db)
    result = edit_service.create_sale(sale_data.dict(), current_user.id, current_user.organization_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.put("/sales/{sale_id}", response_model=Sale, dependencies=[Depends(require_edit_sales())])
async def update_sale(
    request: Request,
    sale_id: UUID,
    sale_data: SaleUpdate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Update a sale record (requires edit_sales permission)"""
    edit_service = EditServiceClass(db)
    result = edit_service.update_sale(
        sale_id, 
        sale_data.dict(exclude_unset=True),
        current_user.id,
        current_user.organization_id
    )
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.delete("/sales/{sale_id}", response_model=Dict[str, str], dependencies=[Depends(require_edit_sales())])
async def delete_sale(
    request: Request,
    sale_id: UUID,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Delete a sale record (requires edit_sales permission)"""
    edit_service = EditServiceClass(db)
    result = edit_service.delete_sale(sale_id, current_user.id, current_user.organization_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_data(
    request: Request,
    current_user: User = Depends(get_authenticated_manager),
    db: Session = Depends(get_db)
):
    """Seed database with sample data (manager role required)"""
    edit_service = EditServiceClass(db)
    result = edit_service.seed_data(current_user.id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result 