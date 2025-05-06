from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from app.db.database import get_db
from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.data_models.Supplier import Supplier
from app.models.service_classes.EditService import EditService
from app.api.mvp.edit_service import MVPEditService
from app.routers.auth import get_current_user
from app.api.mvp.auth import get_manager_user
from app.models.data_models.User import User

# Using the actual service in production, or MVPEditService for development
EditServiceClass = MVPEditService

router = APIRouter(prefix="/edit", tags=["edit"])

# Request models
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
    contact_phone: Optional[str] = None
    lead_time_days: Optional[int] = None
    notes: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    lead_time_days: Optional[int] = None
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

# Product endpoints
@router.post("/products", status_code=status.HTTP_201_CREATED, response_model=Product)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Create a new product (manager role required)"""
    edit_service = EditServiceClass(db)
    result = edit_service.create_product(product_data.dict())
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Update a product (manager role required)"""
    edit_service = EditServiceClass(db)
    result = edit_service.update_product(product_id, product_data.dict(exclude_unset=True))
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.delete("/products/{product_id}", response_model=Dict[str, str])
async def delete_product(
    product_id: UUID,
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Delete a product (manager role required)"""
    edit_service = EditServiceClass(db)
    result = edit_service.delete_product(product_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

# Supplier endpoints
@router.post("/suppliers", status_code=status.HTTP_201_CREATED, response_model=Supplier)
async def create_supplier(
    supplier_data: SupplierCreate,
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Create a new supplier (manager role required)"""
    edit_service = EditServiceClass(db)
    result = edit_service.create_supplier(supplier_data.dict())
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.put("/suppliers/{supplier_id}", response_model=Supplier)
async def update_supplier(
    supplier_id: UUID,
    supplier_data: SupplierUpdate,
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Update a supplier (manager role required)"""
    edit_service = EditServiceClass(db)
    result = edit_service.update_supplier(supplier_id, supplier_data.dict(exclude_unset=True))
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.delete("/suppliers/{supplier_id}", response_model=Dict[str, str])
async def delete_supplier(
    supplier_id: UUID,
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Delete a supplier (manager role required)"""
    edit_service = EditServiceClass(db)
    result = edit_service.delete_supplier(supplier_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/suppliers", response_model=List[Supplier])
async def list_suppliers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all suppliers"""
    suppliers = db.exec(select(Supplier)).all()
    return suppliers

# Sale endpoints
@router.post("/sales", status_code=status.HTTP_201_CREATED, response_model=Sale)
async def create_sale(
    sale_data: SaleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new sale record"""
    edit_service = EditServiceClass(db)
    result = edit_service.create_sale(sale_data.dict())
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.put("/sales/{sale_id}", response_model=Sale)
async def update_sale(
    sale_id: UUID,
    sale_data: SaleUpdate,
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Update a sale record (manager role required)"""
    edit_service = EditServiceClass(db)
    result = edit_service.update_sale(sale_id, sale_data.dict(exclude_unset=True))
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.delete("/sales/{sale_id}", response_model=Dict[str, str])
async def delete_sale(
    sale_id: UUID,
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Delete a sale record (manager role required)"""
    edit_service = EditServiceClass(db)
    result = edit_service.delete_sale(sale_id)
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

# Utility endpoints
@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_data(
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Seed initial data for testing (manager role required)"""
    try:
        # Create default supplier
        default_supplier = Supplier(
            name="Default Supplier",
            contact_email="contact@supplier.com",
            lead_time_days=7
        )
        db.add(default_supplier)
        db.commit()
        db.refresh(default_supplier)
        
        # Return created data
        return {
            "message": "Test data created successfully",
            "supplier": default_supplier
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 