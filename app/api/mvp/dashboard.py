from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pydantic import BaseModel
import random

from app.db.database import get_db
from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.data_models.Supplier import Supplier
from app.models.service_classes.InventoryService import InventoryService
from app.models.service_classes.ThresholdService import ThresholdService
from app.models.service_classes.AnalyticsService import AnalyticsService
from app.routers.auth import get_current_user
from app.models.data_models.User import User

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
async def seed_test_data(db: Session = Depends(get_db)):
    """Seed the database with test data"""
    try:
        # Create a supplier
        supplier = Supplier(
            id=uuid4(),
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
                id=uuid4(),
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
                    id=uuid4(),
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
    # Initialize services with database session
    inventory_service = InventoryService(db)
    threshold_service = ThresholdService(db)
    analytics_service = AnalyticsService(db)
    
    # Get base inventory query
    query = select(Product)
    if search:
        query = query.filter(
            (Product.sku.ilike(f"%{search}%")) | 
            (Product.name.ilike(f"%{search}%"))
        )
    
    # Calculate pagination
    skip = (page - 1) * limit
    total = db.exec(query.count()).first()
    products = db.exec(query.offset(skip).limit(limit)).all()
    
    # Process each product
    inventory_items = []
    for product in products:
        # Get 7-day sales history
        sales_history = analytics_service.get_sales_history(
            product_id=product.id,
            period=7
        )
        
        # Calculate days of stock
        days_of_stock = threshold_service.calculate_days_of_stock(product.id)
        
        # Determine badge and color based on stock level
        badge = None
        color = "#4CAF50"  # Default green
        
        if product.alert_level == "RED":
            badge = "RED"
            color = "#F44336"
        elif product.alert_level == "YELLOW":
            badge = "YELLOW"
            color = "#FFC107"
            
        inventory_items.append({
            "sku": product.sku,
            "name": product.name,
            "on_hand": product.on_hand,
            "reorder_point": product.reorder_point,
            "badge": badge,
            "color": color,
            "sales_trend": [s["quantity"] for s in sales_history],
            "days_of_stock": days_of_stock
        })
    
    return {
        "items": inventory_items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

@router.get("/analytics/sales")
async def get_sales_analytics(
    period: int = Query(7, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sales analytics for the specified period"""
    analytics_service = AnalyticsService(db)
    
    # Get top sellers
    top_sellers = analytics_service.get_top_sellers(limit=5, period=period)
    
    # Calculate overall turnover rate
    turnover_rate = analytics_service.calculate_turnover_rate(period=period)
    
    return {
        "top_sellers": top_sellers,
        "turnover_rate": turnover_rate,
        "period_days": period
    } 