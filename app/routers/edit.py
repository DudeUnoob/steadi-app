from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from sqlmodel import Session, select, func
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
from app.api.mvp.auth import get_current_user, get_manager_user, check_org_membership_and_permissions
from app.routers.inventory import get_org_user_with_permissions


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
@router.get("/products", response_model=List[Product])
async def list_products(
    request: Request,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("view_products"))
):
    """Get all products for the current user's organization"""
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
    logger.info(f"Fetching products for organization {current_user.organization_id} with {len(user_ids)} users")
    
    # Query all products from users in the organization
    products = session.exec(
        select(Product).where(Product.user_id.in_(user_ids))
    ).all()
    
    return products

@router.post("/products", status_code=status.HTTP_201_CREATED, response_model=Product)
async def create_product(
    request: Request,
    product_data: ProductCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("edit_products"))
):
    """Create a new product (requires edit_products permission)"""
    # Ensure user_id is set to current user
    product_data_dict = product_data.dict()
    product_data_dict["user_id"] = current_user.id
    
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
    
    # Check if supplier exists and belongs to the organization
    if product_data.supplier_id:
        supplier = session.exec(
            select(Supplier).where(
                (Supplier.id == product_data.supplier_id) &
                (Supplier.user_id.in_(user_ids))
            )
        ).first()
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier not found in your organization"
            )
    
    # Check if product with same SKU exists in the organization
    existing = session.exec(
        select(Product).where(
            (Product.sku == product_data.sku) &
            (Product.user_id.in_(user_ids))
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A product with this SKU already exists in your organization"
        )
    
    # Create the product
    product = Product(**product_data_dict)
    
    try:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create product: {str(e)}"
        )

@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    request: Request,
    product_id: UUID,
    product_data: ProductUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("edit_products"))
):
    """Update a product (requires edit_products permission)"""
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
    
    # Find product in the organization
    product = session.exec(
        select(Product).where(
            (Product.id == product_id) & 
            (Product.user_id.in_(user_ids))
        )
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in your organization"
        )
    
    # Check if SKU is being updated and if it would conflict with existing SKUs
    if product_data.sku and product_data.sku != product.sku:
        existing = session.exec(
            select(Product).where(
                (Product.sku == product_data.sku) & 
                (Product.user_id.in_(user_ids)) &
                (Product.id != product_id)
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A product with this SKU already exists in your organization"
            )
    
    # If supplier_id is being updated, check if it exists in the organization
    if product_data.supplier_id and product_data.supplier_id != product.supplier_id:
        supplier = session.exec(
            select(Supplier).where(
                (Supplier.id == product_data.supplier_id) &
                (Supplier.user_id.in_(user_ids))
            )
        ).first()
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier not found in your organization"
            )
    
    # Update the product fields
    product_data_dict = product_data.dict(exclude_unset=True)
    for key, value in product_data_dict.items():
        setattr(product, key, value)
    
    try:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )

@router.delete("/products/{product_id}", response_model=Dict[str, str])
async def delete_product(
    request: Request,
    product_id: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("edit_products"))
):
    """Delete a product (requires edit_products permission)"""
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
    
    # Find product in the organization
    product = session.exec(
        select(Product).where(
            (Product.id == product_id) & 
            (Product.user_id.in_(user_ids))
        )
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in your organization"
        )
    
    try:
        product_name = product.name
        session.delete(product)
        session.commit()
        return {"message": f"Product {product_name} deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}"
        )

# Supplier endpoints
@router.get("/suppliers", response_model=List[SupplierWithProductCount])
async def list_suppliers(
    request: Request,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("view_suppliers"))
):
    """Get all suppliers for the current user's organization with product counts"""
    # Get all users in the organization instead of just using current_user.id
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
    logger.info(f"Fetching suppliers for organization {current_user.organization_id} with {len(user_ids)} users")
    
    # Create a custom supplier list with product counts
    suppliers_with_counts = []
    
    # Query all suppliers from users in the organization
    suppliers = session.exec(
        select(Supplier).where(Supplier.user_id.in_(user_ids))
    ).all()
    
    for supplier in suppliers:
        # For each supplier, count products related to this supplier from any user in the organization
        product_count = session.exec(
            select(func.count()).select_from(Product).where(
                (Product.supplier_id == supplier.id) & 
                (Product.user_id.in_(user_ids))
            )
        ).one()
        
        # Create the response object with product count
        supplier_with_count = SupplierWithProductCount(
            id=supplier.id,
            name=supplier.name,
            contact_email=supplier.contact_email,
            phone=supplier.phone,
            lead_time_days=supplier.lead_time_days,
            notes=supplier.notes,
            created_at=supplier.created_at,
            product_count=product_count
        )
        suppliers_with_counts.append(supplier_with_count)
    
    return suppliers_with_counts

@router.post("/suppliers", status_code=status.HTTP_201_CREATED, response_model=Supplier)
async def create_supplier(
    request: Request,
    supplier_data: SupplierCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("edit_suppliers"))
):
    """Create a new supplier (requires edit_suppliers permission)"""
    # Check for duplicate name in the organization FIRST
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
    
    # Check if supplier with same name exists in organization
    existing = session.exec(
        select(Supplier).where(
            (Supplier.name == supplier_data.name) & 
            (Supplier.user_id.in_(user_ids))
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A supplier with this name already exists in your organization"
        )
    
    # Now create the supplier after validation passes
    supplier_data_dict = supplier_data.dict()
    supplier_data_dict["user_id"] = current_user.id
    
    supplier = Supplier(**supplier_data_dict)
    session.add(supplier)
    
    try:
        session.commit()
        session.refresh(supplier)
        return supplier
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create supplier: {str(e)}"
        )

@router.put("/suppliers/{supplier_id}", response_model=Supplier)
async def update_supplier(
    request: Request,
    supplier_id: UUID,
    supplier_data: SupplierUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("edit_suppliers"))
):
    """Update a supplier (requires edit_suppliers permission)"""
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
    
    # Find supplier in the organization
    supplier = session.exec(
        select(Supplier).where(
            (Supplier.id == supplier_id) & 
            (Supplier.user_id.in_(user_ids))
        )
    ).first()
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found in your organization"
        )
    
    # Check if name is being updated and if it would conflict with existing names
    if supplier_data.name and supplier_data.name != supplier.name:
        existing = session.exec(
            select(Supplier).where(
                (Supplier.name == supplier_data.name) & 
                (Supplier.user_id.in_(user_ids)) &
                (Supplier.id != supplier_id)
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A supplier with this name already exists in your organization"
            )
    
    # Save old lead time for product updates if needed
    old_lead_time = supplier.lead_time_days
    
    # Update the supplier fields
    supplier_data_dict = supplier_data.dict(exclude_unset=True)
    for key, value in supplier_data_dict.items():
        setattr(supplier, key, value)
    
    try:
        session.add(supplier)
        session.commit()
        session.refresh(supplier)
        
        # If lead time changed, update products that match the old lead time
        if "lead_time_days" in supplier_data_dict and old_lead_time != supplier.lead_time_days:
            products = session.exec(
                select(Product).where(
                    (Product.supplier_id == supplier_id) & 
                    (Product.lead_time_days == old_lead_time) &
                    (Product.user_id.in_(user_ids))
                )
            ).all()
            
            if products:
                for product in products:
                    product.lead_time_days = supplier.lead_time_days
                    session.add(product)
                
                session.commit()
                logger.info(f"Updated lead time for {len(products)} products from supplier {supplier.name}")
        
        return supplier
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update supplier: {str(e)}"
        )

@router.delete("/suppliers/{supplier_id}", response_model=Dict[str, str])
async def delete_supplier(
    request: Request,
    supplier_id: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("edit_suppliers"))
):
    """Delete a supplier (requires edit_suppliers permission)"""
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
    
    # Find supplier in the organization
    supplier = session.exec(
        select(Supplier).where(
            (Supplier.id == supplier_id) & 
            (Supplier.user_id.in_(user_ids))
        )
    ).first()
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found in your organization"
        )
    
    # Check if supplier has associated products from any user in the organization
    products_count = session.exec(
        select(func.count()).select_from(Product).where(
            (Product.supplier_id == supplier_id) & 
            (Product.user_id.in_(user_ids))
        )
    ).one()
    
    if products_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete supplier with {products_count} associated products"
        )
    
    # Delete the supplier
    try:
        supplier_name = supplier.name
        session.delete(supplier)
        session.commit()
        return {"message": f"Supplier {supplier_name} deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete supplier: {str(e)}"
        )

# Sale endpoints
@router.get("/sales", response_model=List[Sale])
async def list_sales(
    request: Request,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("view_sales"))
):
    """Get all sales for the current user's organization"""
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
    logger.info(f"Fetching sales for organization {current_user.organization_id} with {len(user_ids)} users")
    
    # Query all sales from users in the organization
    sales = session.exec(
        select(Sale).where(Sale.user_id.in_(user_ids))
    ).all()
    
    return sales

@router.post("/sales", status_code=status.HTTP_201_CREATED, response_model=Sale)
async def create_sale(
    request: Request,
    sale_data: SaleCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("edit_sales"))
):
    """Create a new sale record (requires edit_sales permission)"""
    # Ensure user_id is set to current user
    sale_data_dict = sale_data.dict()
    sale_data_dict["user_id"] = current_user.id
    
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
    
    # Verify product exists and belongs to the organization
    product = session.exec(
        select(Product).where(
            (Product.id == sale_data.product_id) &
            (Product.user_id.in_(user_ids))
        )
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in your organization"
        )
    
    # Create the sale
    sale = Sale(**sale_data_dict)
    
    try:
        session.add(sale)
        session.commit()
        session.refresh(sale)
        return sale
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create sale: {str(e)}"
        )

@router.put("/sales/{sale_id}", response_model=Sale)
async def update_sale(
    request: Request,
    sale_id: UUID,
    sale_data: SaleUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("edit_sales"))
):
    """Update a sale record (requires edit_sales permission)"""
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
    
    # Find sale in the organization
    sale = session.exec(
        select(Sale).where(
            (Sale.id == sale_id) & 
            (Sale.user_id.in_(user_ids))
        )
    ).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found in your organization"
        )
    
    # Update the sale fields
    sale_data_dict = sale_data.dict(exclude_unset=True)
    for key, value in sale_data_dict.items():
        setattr(sale, key, value)
    
    try:
        session.add(sale)
        session.commit()
        session.refresh(sale)
        return sale
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sale: {str(e)}"
        )

@router.delete("/sales/{sale_id}", response_model=Dict[str, str])
async def delete_sale(
    request: Request,
    sale_id: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_org_user_with_permissions("edit_sales"))
):
    """Delete a sale record (requires edit_sales permission)"""
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
    
    # Find sale in the organization
    sale = session.exec(
        select(Sale).where(
            (Sale.id == sale_id) & 
            (Sale.user_id.in_(user_ids))
        )
    ).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found in your organization"
        )
    
    try:
        session.delete(sale)
        session.commit()
        return {"message": "Sale deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete sale: {str(e)}"
        )

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