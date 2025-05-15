from sqlmodel import Session, select, func
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
import traceback
from app.models.data_models.Product import Product
from app.models.service_classes.InventoryService import InventoryService
from app.models.service_classes.ThresholdService import ThresholdService
from app.models.service_classes.AnalyticsService import AnalyticsService
from app.models.data_models.Sale import Sale
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

class DashboardService:
    """Service for dashboard-related operations and data retrieval"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)
        self.threshold_service = ThresholdService(db)
        self.analytics_service = AnalyticsService(db)
    
    def get_inventory_dashboard(self, search: Optional[str] = None, page: int = 1, limit: int = 50, user_id: UUID = None) -> Dict[str, Any]:
        """
        Get paginated inventory dashboard with search and analytics
        Returns items:[{sku, name, on_hand, reorder_point, badge, color, sales_trend, days_of_stock}]
        """
        try:
            logger.info(f"Fetching inventory dashboard - search: {search}, page: {page}, limit: {limit}, user_id: {user_id}")
            
            # Get base inventory query
            query = select(Product)
            
            # Apply user filter if provided
            if user_id:
                query = query.where(Product.user_id == user_id)
                logger.debug(f"Applied user filter: {user_id}")
                
            if search:
                # Special case handling for "Candle X" type searches, to avoid "Candle 1" matching "Candle 11", etc.
                import re
                # Check if search is in format "Something X" where X is a number
                pattern = r"^(.+)(\s+)(\d+)$"
                match = re.match(pattern, search)
                
                if match:
                    # Extract the base name and number
                    base_name = match.group(1)
                    space = match.group(2) 
                    number = match.group(3)
                    
                    # Create a precise pattern: base_name + space + exact number + boundary
                    query = query.filter(
                        (Product.sku == search) | 
                        (Product.name == search) |
                        # This specifically matches "Candle 1" but not "Candle 11", etc.
                        (Product.name.ilike(f"{base_name}{space}{number}"))
                    )
                    logger.debug(f"Applied numeric pattern search: {base_name}{space}{number}")
                else:
                    # Default search for non-numeric patterns
                    query = query.filter(
                        (Product.sku == search) | 
                        (Product.name == search) |
                        # Also include pattern matches with space-aware boundaries
                        (Product.name.ilike(f"{search} %")) |
                        (Product.name.ilike(f"% {search} %")) |
                        (Product.name.ilike(f"% {search}"))
                    )
                    logger.debug(f"Applied general search pattern: {search}")
            
            # Count total items
            count_query = select(func.count()).select_from(Product)
            
            # Apply user filter to count query
            if user_id:
                count_query = count_query.where(Product.user_id == user_id)
                
            if search:
                # Same special case handling for count query
                import re
                pattern = r"^(.+)(\s+)(\d+)$"
                match = re.match(pattern, search)
                
                if match:
                    base_name = match.group(1)
                    space = match.group(2)
                    number = match.group(3)
                    
                    count_query = count_query.where(
                        (Product.sku == search) | 
                        (Product.name == search) |
                        (Product.name.ilike(f"{base_name}{space}{number}"))
                    )
                else:
                    count_query = count_query.where(
                        (Product.sku == search) | 
                        (Product.name == search) |
                        (Product.name.ilike(f"{search} %")) |
                        (Product.name.ilike(f"% {search} %")) |
                        (Product.name.ilike(f"% {search}"))
                    )
                    
            logger.debug("Executing count query")
            try:
                total = self.db.exec(count_query).one()
                logger.debug(f"Total products found: {total}")
            except Exception as e:
                logger.error(f"Error executing count query: {str(e)}")
                total = 0
            
            # Calculate pagination
            skip = (page - 1) * limit
            
            logger.debug(f"Executing products query with offset {skip} and limit {limit}")
            try:
                products = self.db.exec(query.offset(skip).limit(limit)).all()
                logger.debug(f"Retrieved {len(products)} products")
            except Exception as e:
                logger.error(f"Error retrieving products: {str(e)}")
                products = []
            
            # Get product IDs for batch processing
            product_ids = [product.id for product in products]
            
            if not product_ids:
                logger.debug("No products found, returning empty result")
                return {
                    "items": [],
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "pages": (total + limit - 1) // limit if total > 0 else 0
                }
            
            logger.debug("Fetching batch sales history")
            # Get sales history for all products in one query, with user_id filter
            try:
                batch_sales_history = self.analytics_service.get_batch_sales_history(
                    product_ids, 
                    period=7,
                    user_id=user_id
                )
                logger.debug(f"Retrieved sales history for {len(batch_sales_history)} products")
            except Exception as e:
                logger.error(f"Error fetching batch sales history: {str(e)}")
                # Provide an empty sales history as fallback
                batch_sales_history = {product_id: [] for product_id in product_ids}
            
            logger.debug("Calculating batch days of stock")
            # Get days of stock for all products in one query
            try:
                batch_days_of_stock = self.threshold_service.calculate_batch_days_of_stock(
                    product_ids,
                    user_id=user_id
                )
                logger.debug(f"Retrieved days of stock for {len(batch_days_of_stock)} products")
            except Exception as e:
                logger.error(f"Error calculating batch days of stock: {str(e)}")
                # Provide a default days of stock value as fallback
                batch_days_of_stock = {product_id: 0 for product_id in product_ids}
            
            # Process each product (now using the batch results)
            inventory_items = []
            for product in products:
                # Get data from batch results
                sales_history = batch_sales_history.get(product.id, [])
                days_of_stock = batch_days_of_stock.get(product.id, 0)
                
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
                    "sales_trend": [s.get("quantity", 0) if isinstance(s, dict) else 0 for s in sales_history],
                    "days_of_stock": days_of_stock
                })
            
            logger.info(f"Successfully built inventory dashboard with {len(inventory_items)} items")
            return {
                "items": inventory_items,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error in get_inventory_dashboard: {str(e)}")
            logger.error(traceback.format_exc())
            # Return a minimal valid response
            return {
                "items": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0,
                "error": str(e)
            }
    
    def get_sales_analytics(self, period: int = 7, user_id: UUID = None) -> Dict[str, Any]:
        """Get sales analytics for the specified period"""
        try:
            logger.info(f"Fetching sales analytics for period {period}, user_id: {user_id}")
            
            # Get top sellers
            try:
                top_sellers = self.analytics_service.get_top_sellers(
                    limit=5, 
                    period=period,
                    user_id=user_id
                )
                logger.debug(f"Retrieved {len(top_sellers)} top sellers")
            except Exception as e:
                logger.error(f"Error fetching top sellers: {str(e)}")
                top_sellers = []
            
            # Calculate overall turnover rate
            try:
                turnover_rate = self.analytics_service.calculate_turnover_rate(
                    period=period,
                    user_id=user_id
                )
                logger.debug(f"Calculated turnover rate: {turnover_rate.get('overall_turnover_rate', 0)}")
            except Exception as e:
                logger.error(f"Error calculating turnover rate: {str(e)}")
                turnover_rate = {
                    "overall_turnover_rate": 0,
                    "total_cost_of_goods_sold": 0,
                    "total_inventory_value": 0,
                    "products": {}
                }
            
            logger.info("Successfully built sales analytics")
            return {
                "top_sellers": top_sellers,
                "turnover_rate": turnover_rate,
                "period_days": period
            }
            
        except Exception as e:
            logger.error(f"Error in get_sales_analytics: {str(e)}")
            logger.error(traceback.format_exc())
            # Return a minimal valid response
            return {
                "top_sellers": [],
                "turnover_rate": {
                    "overall_turnover_rate": 0,
                    "total_cost_of_goods_sold": 0,
                    "total_inventory_value": 0,
                    "products": {}
                },
                "period_days": period,
                "error": str(e)
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