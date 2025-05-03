from uuid import UUID
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlmodel import Session, select, func
from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.enums.AlertLevel import AlertLevel

class ThresholdService:
    """Evaluates inventory thresholds and generates alerts"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def evaluate_thresholds(self, product_id: Optional[UUID] = None) -> List[Dict]:
        """Evaluate thresholds for one or all products"""
        query = select(Product)
        if product_id:
            query = query.where(Product.id == product_id)
            
        products = self.db.exec(query).all()
        results = []
        
        for product in products:
            days_of_stock = self.calculate_days_of_stock(product.id)
            reorder_point = self.calculate_reorder_point(product.id)
            
            # Determine alert level
            alert_level = None
            if product.on_hand <= reorder_point:
                alert_level = AlertLevel.RED
            elif product.on_hand <= (reorder_point + product.safety_stock):
                alert_level = AlertLevel.YELLOW
                
            results.append({
                "product_id": product.id,
                "sku": product.sku,
                "name": product.name,
                "on_hand": product.on_hand,
                "reorder_point": reorder_point,
                "days_of_stock": days_of_stock,
                "alert_level": alert_level
            })
            
        return results
    
    def calculate_reorder_point(self, product_id: UUID) -> int:
        """Calculate reorder point based on formula"""
        product = self.db.get(Product, product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
            
        # Get average daily sales
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sales_query = select(func.sum(Sale.quantity)).where(
            Sale.product_id == product_id,
            Sale.sale_date >= thirty_days_ago
        )
        total_sales = self.db.exec(sales_query).first() or 0
        avg_daily_sales = total_sales / 30
        
        # Calculate reorder point
        reorder_point = product.safety_stock + (avg_daily_sales * product.lead_time_days)
        return max(0, int(reorder_point))
    
    def calculate_days_of_stock(self, product_id: UUID) -> float:
        """Calculate estimated days of stock remaining"""
        product = self.db.get(Product, product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
            
        # Get average daily sales
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sales_query = select(func.sum(Sale.quantity)).where(
            Sale.product_id == product_id,
            Sale.sale_date >= thirty_days_ago
        )
        total_sales = self.db.exec(sales_query).first() or 0
        avg_daily_sales = total_sales / 30
        
        if avg_daily_sales == 0:
            return float('inf')
            
        return product.on_hand / avg_daily_sales
