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
            # Calculate reorder point if needed
            if product.reorder_point == 0:
                product.reorder_point = self.calculate_reorder_point(product.id)
                self.db.add(product)
            
            # Determine alert level
            old_alert_level = product.alert_level
            
            if product.on_hand <= product.reorder_point:
                product.alert_level = AlertLevel.RED
            elif product.on_hand <= (product.reorder_point + product.safety_stock):
                product.alert_level = AlertLevel.YELLOW
            else:
                product.alert_level = None
            
            # Save if alert level changed
            if old_alert_level != product.alert_level:
                self.db.add(product)
            
            results.append({
                "product_id": product.id,
                "sku": product.sku,
                "name": product.name,
                "on_hand": product.on_hand,
                "reorder_point": product.reorder_point,
                "safety_stock": product.safety_stock,
                "alert_level": product.alert_level
            })
        
        # Commit all changes at once
        self.db.commit()
        
        return results
    
    def calculate_reorder_point(self, product_id: UUID) -> int:
        """Calculate reorder point based on formula:
        reorder_point = safety_stock + (avg_daily_sales × lead_time_days)
        """
        # Get product
        product = self.db.exec(select(Product).where(Product.id == product_id)).first()
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Calculate average daily sales over the past 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Get total sales for the period
        query = select(func.sum(Sale.quantity)).where(
            (Sale.product_id == product_id) & 
            (Sale.sale_date >= thirty_days_ago)
        )
        total_sales = self.db.exec(query).first() or 0
        
        # Calculate average daily sales
        avg_daily_sales = total_sales / 30
        
        # Calculate reorder point (minimum of 1)
        reorder_point = max(1, product.safety_stock + round(avg_daily_sales * product.lead_time_days))
        
        return reorder_point
    
    def calculate_days_of_stock(self, product_id: UUID) -> float:
        """Calculate estimated days of stock remaining
        days_of_stock = on_hand ÷ avg_daily_sales
        """
        # Get product
        product = self.db.exec(select(Product).where(Product.id == product_id)).first()
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Calculate average daily sales over the past 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Get total sales for the period
        query = select(func.sum(Sale.quantity)).where(
            (Sale.product_id == product_id) & 
            (Sale.sale_date >= thirty_days_ago)
        )
        total_sales = self.db.exec(query).first() or 0
        
        # Calculate average daily sales (minimum of 0.1 to avoid division by zero)
        avg_daily_sales = max(0.1, total_sales / 30)
        
        # Calculate days of stock
        days_of_stock = product.on_hand / avg_daily_sales
        
        return round(days_of_stock, 1)
