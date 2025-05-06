from sqlmodel import Session, select, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.models.data_models.Product import Product
from app.models.service_classes.InventoryService import InventoryService
from app.models.service_classes.ThresholdService import ThresholdService
from app.models.service_classes.AnalyticsService import AnalyticsService

class DashboardService:
    """Service for dashboard-related operations and data retrieval"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)
        self.threshold_service = ThresholdService(db)
        self.analytics_service = AnalyticsService(db)
    
    def get_inventory_dashboard(self, search: Optional[str] = None, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Get paginated inventory dashboard with search and analytics
        Returns items:[{sku, name, on_hand, reorder_point, badge, color, sales_trend, days_of_stock}]
        """
        # Get base inventory query
        query = select(Product)
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
        
        # Count total items
        count_query = select(func.count()).select_from(Product)
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
        total = self.db.exec(count_query).one()
        
        # Calculate pagination
        skip = (page - 1) * limit
        products = self.db.exec(query.offset(skip).limit(limit)).all()
        
        # Get product IDs for batch processing
        product_ids = [product.id for product in products]
        
        # Get sales history for all products in one query
        batch_sales_history = self.analytics_service.get_batch_sales_history(product_ids, period=7)
        
        # Get days of stock for all products in one query
        batch_days_of_stock = self.threshold_service.calculate_batch_days_of_stock(product_ids)
        
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
    
    def get_sales_analytics(self, period: int = 7) -> Dict[str, Any]:
        """Get sales analytics for the specified period"""
        # Get top sellers
        top_sellers = self.analytics_service.get_top_sellers(limit=5, period=period)
        
        # Calculate overall turnover rate
        turnover_rate = self.analytics_service.calculate_turnover_rate(period=period)
        
        return {
            "top_sellers": top_sellers,
            "turnover_rate": turnover_rate,
            "period_days": period
        }
    
    def seed_test_data(self) -> Dict[str, str]:
        """Delegate to appropriate services to seed test data"""
        # This would typically call methods from inventory, supplier, and sales services
        # For simplicity, we'll just return a message
        return {"message": "Test data creation should be handled by specialized services"} 