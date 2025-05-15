from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging

from app.db.database import get_db
from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.data_models.Supplier import Supplier
from app.models.data_models.User import User
from app.models.service_classes.DashboardService import DashboardService
from app.api.auth.supabase import get_current_supabase_user, get_optional_supabase_user
from app.routers.auth import get_current_user, get_owner_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class InventoryItemResponse(BaseModel):
    sku: str
    name: str
    on_hand: int
    reorder_point: int
    badge: Optional[str]  
    color: str 
    sales_trend: List[float]  
    days_of_stock: float
    
class SaleItemResponse(BaseModel):
    product_id: str
    sku: str
    name: str
    quantity: int
    sale_date: datetime
    revenue: float
    
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
        from sqlmodel import select
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

@router.get("/inventory", response_model=dict)
async def get_inventory_dashboard(
    request: Request,
    search: Optional[str] = Query(None, description="Search by SKU or product name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated inventory dashboard with search and analytics
    Returns items:[{sku, name, on_hand, reorder_point, badge, color}]
    NFR: Initial load ≤ 200ms, search filter updates ≤ 100ms
    """
    dashboard_service = DashboardService(db)
    return dashboard_service.get_inventory_dashboard(
        search=search,
        page=page,
        limit=limit,
        user_id=current_user.id
    )

@router.get("/analytics/sales", response_model=Dict[str, Any])
async def get_sales_analytics(
    request: Request,
    period: int = Query(7, description="Number of days to analyze"),
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Get sales analytics for the specified period
    Returns:
    - top_sellers: [{product_id, sku, name, quantity_sold, revenue}]
    - turnover_rate: overall inventory turnover statistics
    - period_days: the analysis period
    """
    dashboard_service = DashboardService(db)
    return dashboard_service.get_sales_analytics(
        period=period, 
        user_id=current_user.id
    )

@router.get("/sales", response_model=Dict[str, Any])
async def get_sales(
    request: Request,
    period: int = Query(7, description="Number of days to retrieve sales data for"),
    product_id: Optional[UUID] = Query(None, description="Optional product ID to filter sales"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Get sales data for the specified period
    Returns:
    - items: [{product_id, sku, name, quantity, sale_date, revenue}]
    - total: total number of records
    - page: current page
    - limit: items per page
    - pages: total number of pages
    - daily_totals: [{date, total_revenue, total_quantity}]
    """
    try:
        logger.info(f"Fetching sales data - period: {period}, product_id: {product_id}, page: {page}, limit: {limit}")
        dashboard_service = DashboardService(db)
        return dashboard_service.get_sales_data(
            period=period,
            product_id=product_id,
            page=page,
            limit=limit,
            user_id=current_user.id
        )
    except Exception as e:
        logger.error(f"Error fetching sales data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sales data: {str(e)}") 