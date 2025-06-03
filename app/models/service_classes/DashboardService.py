from sqlmodel import Session, select, func, text
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
import traceback
from functools import lru_cache
import time
from app.models.data_models.Product import Product
from app.models.service_classes.InventoryService import InventoryService
from app.models.service_classes.ThresholdService import ThresholdService
from app.models.service_classes.AnalyticsService import AnalyticsService
from app.models.data_models.Sale import Sale
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

# Simple in-memory cache with TTL
_cache = {}
_cache_ttl = {}
CACHE_DURATION = 300  # 5 minutes

def cached_method(ttl: int = CACHE_DURATION):
    """Decorator for caching method results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args[1:]) + str(kwargs))}"
            current_time = time.time()
            
            # Check if cached result exists and is still valid
            if cache_key in _cache and cache_key in _cache_ttl:
                if current_time - _cache_ttl[cache_key] < ttl:
                    logger.debug(f"Cache hit: {cache_key}")
                    return _cache[cache_key]
                else:
                    # Remove expired cache entry
                    del _cache[cache_key]
                    del _cache_ttl[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_ttl[cache_key] = current_time
            logger.debug(f"Cache miss: {cache_key}")
            
            return result
        return wrapper
    return decorator

class DashboardService:
    """Service for dashboard-related operations and data retrieval"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)
        self.threshold_service = ThresholdService(db)
        self.analytics_service = AnalyticsService(db)
    
    @cached_method(ttl=120)  # Cache for 2 minutes
    def get_inventory_dashboard(self, search: Optional[str] = None, page: int = 1, limit: int = 50, user_id: UUID = None) -> Dict[str, Any]:
        """
        Get paginated inventory dashboard with search and analytics
        Optimized with query improvements and caching
        """
        try:
            logger.info(f"Fetching inventory dashboard - search: {search}, page: {page}, limit: {limit}, user_id: {user_id}")
            
            # Use optimized query with proper indexing hints
            base_query = select(Product)
            count_query = select(func.count(Product.id))
            
            # Apply user filter first (most selective)
            if user_id:
                base_query = base_query.where(Product.user_id == user_id)
                count_query = count_query.where(Product.user_id == user_id)
                logger.debug(f"Applied user filter: {user_id}")
            
            # Apply search filters with optimized patterns
            if search:
                search_filter = self._build_optimized_search_filter(search)
                base_query = base_query.where(search_filter)
                count_query = count_query.where(search_filter)
                logger.debug(f"Applied search filter: {search}")
            
            # Get total count efficiently
            logger.debug("Executing optimized count query")
            try:
                total = self.db.exec(count_query).one()
                logger.debug(f"Total products found: {total}")
            except Exception as e:
                logger.error(f"Error executing count query: {str(e)}")
                total = 0
            
            if total == 0:
                return {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "limit": limit,
                    "pages": 0
                }
            
            # Calculate pagination
            skip = (page - 1) * limit
            
            # Execute main query with ordering for consistent pagination
            logger.debug(f"Executing products query with offset {skip} and limit {limit}")
            try:
                products = self.db.exec(
                    base_query
                    .order_by(Product.name)  # Consistent ordering
                    .offset(skip)
                    .limit(limit)
                ).all()
                logger.debug(f"Retrieved {len(products)} products")
            except Exception as e:
                logger.error(f"Error retrieving products: {str(e)}")
                products = []
            
            if not products:
                return {
                    "items": [],
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "pages": (total + limit - 1) // limit if total > 0 else 0
                }
            
            # Batch process all analytics data to avoid N+1 queries
            product_ids = [product.id for product in products]
            
            logger.debug("Fetching batch analytics data")
            start_time = time.time()
            
            # Fetch all required data in parallel where possible
            try:
                batch_sales_history = self.analytics_service.get_batch_sales_history(
                    product_ids, 
                    period=7,
                    user_id=user_id
                )
                logger.debug(f"Retrieved sales history in {time.time() - start_time:.3f}s")
                
                batch_days_of_stock = self.threshold_service.calculate_batch_days_of_stock(
                    product_ids,
                    user_id=user_id
                )
                logger.debug(f"Retrieved days of stock in {time.time() - start_time:.3f}s")
                
            except Exception as e:
                logger.error(f"Error fetching batch analytics: {str(e)}")
                # Provide fallback data
                batch_sales_history = {product_id: [] for product_id in product_ids}
                batch_days_of_stock = {product_id: 0 for product_id in product_ids}
            
            # Process products efficiently
            inventory_items = []
            for product in products:
                # Get batch data with fallbacks
                sales_history = batch_sales_history.get(product.id, [])
                days_of_stock = batch_days_of_stock.get(product.id, 0)
                
                # Optimize badge and color determination
                badge, color = self._get_product_status(product)
                
                inventory_items.append({
                    "sku": product.sku,
                    "name": product.name,
                    "on_hand": product.on_hand,
                    "reorder_point": product.reorder_point,
                    "badge": badge,
                    "color": color,
                    "sales_trend": [s.get("quantity", 0) if isinstance(s, dict) else 0 for s in sales_history],
                    "days_of_stock": days_of_stock
                })
            
            pages = (total + limit - 1) // limit if total > 0 else 0
            
            logger.info(f"Successfully built inventory dashboard with {len(inventory_items)} items in {time.time() - start_time:.3f}s")
            return {
                "items": inventory_items,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in get_inventory_dashboard: {str(e)}")
            logger.error(traceback.format_exc())
            raise e
    
    def _build_optimized_search_filter(self, search: str):
        """Build optimized search filter with proper indexing"""
        import re
        
        # Handle numeric patterns efficiently
        pattern = r"^(.+)(\s+)(\d+)$"
        match = re.match(pattern, search)
        
        if match:
            base_name = match.group(1)
            space = match.group(2)
            number = match.group(3)
            
            return (
                (Product.sku == search) | 
                (Product.name == search) |
                (Product.name.like(f"{base_name}{space}{number}"))
            )
        else:
            # Use ILIKE for case-insensitive search with proper indexing
            return (
                (Product.sku.ilike(f"%{search}%")) | 
                (Product.name.ilike(f"%{search}%"))
            )
    
    def _get_product_status(self, product: Product) -> tuple[Optional[str], str]:
        """Efficiently determine product status badge and color"""
        if hasattr(product, 'alert_level'):
            if product.alert_level == "RED":
                return "RED", "#F44336"
            elif product.alert_level == "YELLOW":
                return "YELLOW", "#FFC107"
        
        return None, "#4CAF50"  # Default green
    
    @cached_method(ttl=180)  # Cache for 3 minutes
    def get_sales_analytics(self, period: int = 7, user_id: UUID = None) -> Dict[str, Any]:
        """
        Get sales analytics with improved query performance and caching
        """
        try:
            logger.info(f"Fetching sales analytics - period: {period}, user_id: {user_id}")
            start_time = time.time()
            
            # Use analytics service with optimized queries
            analytics_result = self.analytics_service.get_sales_analytics(
                period=period,
                user_id=user_id
            )
            
            logger.info(f"Sales analytics retrieved in {time.time() - start_time:.3f}s")
            return analytics_result
            
        except Exception as e:
            logger.error(f"Error fetching sales analytics: {str(e)}")
            logger.error(traceback.format_exc())
            # Return default structure on error
            return {
                "top_sellers": [],
                "turnover_rate": 0.0,
                "monthly_sales": [],
                "active_orders": 0,
                "period_days": period
            }
    
    def get_sales_data(self, period: int = 7, product_id: Optional[UUID] = None, page: int = 1, limit: int = 50, user_id: UUID = None) -> Dict[str, Any]:
        """
        Get detailed sales data for the specified period
        Returns paginated sales records with daily totals
        """
        try:
            logger.info(f"Fetching sales data for period {period}, product_id: {product_id}, user_id: {user_id}")
            
            # Define date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period)
            
            # Base query for sales with product join for details
            query = select(
                Sale.id,
                Sale.product_id,
                Sale.quantity,
                Sale.sale_date,
                Product.sku,
                Product.name,
                Product.cost
            ).join(
                Product, Sale.product_id == Product.id
            ).where(
                (Sale.sale_date >= start_date) &
                (Sale.sale_date <= end_date)
            )
            
            # Apply user filter if provided
            if user_id:
                query = query.where(Sale.user_id == user_id)
            
            # Apply product filter if provided
            if product_id:
                query = query.where(Sale.product_id == product_id)
                
            # Count total records for pagination
            count_query = select(func.count()).select_from(
                select(Sale.id).where(Sale.sale_date >= start_date).where(Sale.sale_date <= end_date)
            )
            
            # Apply user filter to count query
            if user_id:
                count_query = count_query.where(Sale.user_id == user_id)
                
            # Apply product filter to count query if provided
            if product_id:
                count_query = count_query.where(Sale.product_id == product_id)
            
            try:
                total = self.db.exec(count_query).one()
                logger.debug(f"Total sales records: {total}")
            except Exception as e:
                logger.error(f"Error executing count query: {str(e)}")
                total = 0
            
            # Calculate pagination
            skip = (page - 1) * limit
            
            # Apply pagination to the query
            query = query.order_by(Sale.sale_date.desc()).offset(skip).limit(limit)
            
            # Execute the query
            logger.debug(f"Executing sales query with offset {skip} and limit {limit}")
            try:
                sales_records = self.db.exec(query).all()
                logger.debug(f"Retrieved {len(sales_records)} sales records")
            except Exception as e:
                logger.error(f"Error retrieving sales records: {str(e)}")
                sales_records = []
            
            # Process sales records
            items = []
            for record in sales_records:
                revenue = record.quantity * record.cost
                items.append({
                    "id": str(record.id),
                    "product_id": str(record.product_id),
                    "sku": record.sku,
                    "name": record.name,
                    "quantity": record.quantity,
                    "sale_date": record.sale_date.isoformat(),
                    "revenue": round(revenue, 2)
                })
            
            # Get daily totals
            daily_query = select(
                func.date_trunc('day', Sale.sale_date).label("date"),
                func.sum(Sale.quantity * Product.cost).label("revenue"),
                func.sum(Sale.quantity).label("quantity")
            ).join(
                Product, Sale.product_id == Product.id
            ).where(
                (Sale.sale_date >= start_date) &
                (Sale.sale_date <= end_date)
            )
            
            # Apply user filter if provided
            if user_id:
                daily_query = daily_query.where(Sale.user_id == user_id)
                
            # Apply product filter if provided
            if product_id:
                daily_query = daily_query.where(Sale.product_id == product_id)
                
            daily_query = daily_query.group_by(
                func.date_trunc('day', Sale.sale_date)
            ).order_by(
                func.date_trunc('day', Sale.sale_date)
            )
            
            try:
                daily_results = self.db.exec(daily_query).all()
                logger.debug(f"Retrieved daily totals for {len(daily_results)} days")
            except Exception as e:
                logger.error(f"Error retrieving daily totals: {str(e)}")
                daily_results = []
            
            # Process daily totals
            daily_totals = []
            for result in daily_results:
                daily_totals.append({
                    "date": result.date.strftime("%Y-%m-%d"),
                    "revenue": round(result.revenue or 0, 2),
                    "quantity": int(result.quantity or 0)
                })
            
            # Calculate monthly revenue (additional feature based on PRD)
            monthly_query = select(
                func.date_trunc('month', Sale.sale_date).label("month"),
                func.sum(Sale.quantity * Product.cost).label("revenue")
            ).join(
                Product, Sale.product_id == Product.id
            ).where(
                Sale.sale_date >= start_date - timedelta(days=30)  # Include previous month
            )
            
            # Apply user filter if provided
            if user_id:
                monthly_query = monthly_query.where(Sale.user_id == user_id)
                
            monthly_query = monthly_query.group_by(
                func.date_trunc('month', Sale.sale_date)
            ).order_by(
                func.date_trunc('month', Sale.sale_date)
            )
            
            try:
                monthly_results = self.db.exec(monthly_query).all()
                logger.debug(f"Retrieved monthly totals for {len(monthly_results)} months")
            except Exception as e:
                logger.error(f"Error retrieving monthly totals: {str(e)}")
                monthly_results = []
            
            # Process monthly totals
            monthly_sales = []
            for result in monthly_results:
                monthly_sales.append({
                    "month": result.month.strftime("%Y-%m"),
                    "revenue": round(result.revenue or 0, 2)
                })
            
            logger.info(f"Successfully built sales data with {len(items)} records")
            return {
                "items": items,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if total > 0 else 0,
                "daily_totals": daily_totals,
                "monthly_sales": monthly_sales,
                "period_days": period
            }
            
        except Exception as e:
            logger.error(f"Error in get_sales_data: {str(e)}")
            logger.error(traceback.format_exc())
            # Return a minimal valid response
            return {
                "items": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0,
                "daily_totals": [],
                "monthly_sales": [],
                "period_days": period,
                "error": str(e)
            }
    
    def seed_test_data(self, user_id: UUID) -> Dict[str, str]:
        """Delegate to appropriate services to seed test data"""
        # This would typically call methods from inventory, supplier, and sales services
        # For simplicity, we'll just return a message
        return {
            "message": "Test data creation should be handled by specialized services",
            "user_id": str(user_id) if user_id else None
        } 