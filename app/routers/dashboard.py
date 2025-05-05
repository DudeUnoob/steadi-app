from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import random

from app.db.database import get_db
from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.data_models.Supplier import Supplier
from app.models.data_models.User import User
from app.models.service_classes.DashboardService import DashboardService
from app.routers.auth import get_current_user, get_owner_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Response model for inventory items
class InventoryItemResponse(BaseModel):
    sku: str
    name: str
    on_hand: int
    reorder_point: int
    badge: Optional[str]  # RED, YELLOW, or None
    color: str  # Hex color code for visual representation
    sales_trend: List[float]  # Last 7 days sales data
    days_of_stock: float

@router.post("/test/seed")
async def seed_test_data(
    current_user: User = Depends(get_owner_user),
    db: Session = Depends(get_db)
):
    """Seed the database with test data (owner role required)"""
    try:
        # Create a supplier
        supplier = Supplier(
            name="Test Supplier",
            contact_email="supplier@test.com",
            lead_time_days=7
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        
        # Create some products
        products = []
        for i in range(10):
            product = Product(
                sku=f"TEST-{i:03d}",
                name=f"Test Product {i}",
                supplier_id=supplier.id,
                cost=random.uniform(10, 100),
                on_hand=random.randint(0, 100),
                reorder_point=random.randint(10, 30),
                safety_stock=random.randint(5, 15),
                lead_time_days=7
            )
            products.append(product)
            db.add(product)
        
        db.commit()
        
        # Create sales data for the last 30 days
        for product in products:
            for i in range(30):
                sale_date = datetime.utcnow() - timedelta(days=i)
                sale = Sale(
                    product_id=product.id,
                    quantity=random.randint(0, 5),
                    sale_date=sale_date
                )
                db.add(sale)
        
        db.commit()
        return {"message": "Test data created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory", response_model=dict)
async def get_inventory_dashboard(
    search: Optional[str] = Query(None, description="Search by SKU or product name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated inventory dashboard with search and analytics
    Returns items:[{sku, name, on_hand, reorder_point, badge, color}]
    NFR: Initial load ≤ 200ms, search filter updates ≤ 100ms
    """
    # Use the dashboard service to retrieve data
    dashboard_service = DashboardService(db)
    return dashboard_service.get_inventory_dashboard(
        search=search,
        page=page,
        limit=limit
    )

@router.get("/analytics/sales")
async def get_sales_analytics(
    period: int = Query(7, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sales analytics for the specified period"""
    dashboard_service = DashboardService(db)
    return dashboard_service.get_sales_analytics(period=period) 