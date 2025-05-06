from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import random
import re

from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.data_models.Supplier import Supplier
from app.models.service_classes.InventoryService import InventoryService
from app.models.service_classes.ThresholdService import ThresholdService
from app.models.service_classes.AnalyticsService import AnalyticsService

class MVPDashboardService:
    """Legacy dashboard service for MVP features"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)
        self.threshold_service = ThresholdService(db)
        self.analytics_service = AnalyticsService(db)
    
    def seed_test_data(self) -> Dict[str, str]:
        """Seed the database with test data"""
        try:
            # Create a supplier
            supplier = Supplier(
                name="Test Supplier",
                contact_email="supplier@test.com",
                lead_time_days=7
            )
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            
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
                self.db.add(product)
            
            self.db.commit()
            
            # Create sales data for the last 30 days
            for product in products:
                for i in range(30):
                    sale_date = datetime.utcnow() - timedelta(days=i)
                    sale = Sale(
                        product_id=product.id,
                        quantity=random.randint(0, 5),
                        sale_date=sale_date
                    )
                    self.db.add(sale)
            
            self.db.commit()
            return {"message": "Test data created successfully"}
            
        except Exception as e:
            return {"error": str(e)}

    def get_inventory_dashboard(self, search: Optional[str] = None, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Get paginated inventory dashboard with search and analytics
        Returns items:[{sku, name, on_hand, reorder_point, badge, color, sales_trend, days_of_stock}]
        """
        # Get base inventory query
        query = select(Product)
        if search:
            # Special case handling for "Candle X" type searches, to avoid "Candle 1" matching "Candle 11", etc.
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
            # Check if search is in format "Something X" where X is a number
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
        
        # Process each product
        inventory_items = []
        for product in products:
            # Get 7-day sales history
            sales_history = self.analytics_service.get_sales_history(
                product_id=product.id,
                period=7
            )
            
            # Calculate days of stock
            days_of_stock = self.threshold_service.calculate_days_of_stock(product.id)
            
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