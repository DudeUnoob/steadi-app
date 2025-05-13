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
        """
        Evaluate thresholds for one or all products using the formula from PRD section 3.3:
        - Formula: reorder_point = safety_stock + (avg_daily_sales × lead_time_days)
        - Set alert level:
          - RED if on_hand <= reorder_point
          - YELLOW if on_hand <= reorder_point + safety_stock
        """
        query = select(Product)
        if product_id:
            query = query.where(Product.id == product_id)
        
        products = self.db.exec(query).all()
        product_ids = [product.id for product in products]
        
        # Get days of stock for all products in one query
        days_of_stock_map = self.calculate_batch_days_of_stock(product_ids)
        
        results = []
        for product in products:
            # Calculate and update reorder point
            new_reorder_point = self.calculate_reorder_point(product.id)
            if product.reorder_point != new_reorder_point:
                product.reorder_point = new_reorder_point
                self.db.add(product)
            
            # Determine alert level
            old_alert_level = product.alert_level
            
            if product.on_hand <= product.reorder_point:
                new_alert_level = AlertLevel.RED
            elif product.on_hand <= (product.reorder_point + product.safety_stock):
                new_alert_level = AlertLevel.YELLOW
            else:
                new_alert_level = None
            
            # Update alert level if changed
            if old_alert_level != new_alert_level:
                product.alert_level = new_alert_level
                self.db.add(product)
            
            # Get days of stock
            days_of_stock = days_of_stock_map.get(product.id, 0)
            
            results.append({
                "product_id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "on_hand": product.on_hand,
                "old_reorder_point": product.reorder_point if product.reorder_point == new_reorder_point else new_reorder_point,
                "new_reorder_point": new_reorder_point,
                "safety_stock": product.safety_stock,
                "lead_time_days": product.lead_time_days,
                "alert_level": product.alert_level,
                "days_of_stock": days_of_stock,
                "needs_immediate_action": product.alert_level == AlertLevel.RED or days_of_stock < product.lead_time_days
            })
        
        # Commit all changes at once
        self.db.commit()
        
        return results
    
    def calculate_batch_days_of_stock(self, product_ids: List[UUID]) -> Dict[UUID, float]:
        """Calculate days of stock for multiple products at once"""
        if not product_ids:
            return {}
            
        # Get all products in one query
        products = self.db.exec(select(Product).where(Product.id.in_(product_ids))).all()
        product_map = {product.id: product for product in products}
        
        # Calculate average daily sales over the past 30 days for all products
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Get total sales for all products in one query
        sales_query = select(
            Sale.product_id,
            func.sum(Sale.quantity).label("total_quantity")
        ).where(
            (Sale.product_id.in_(product_ids)) & 
            (Sale.sale_date >= thirty_days_ago)
        ).group_by(Sale.product_id)
        
        # Create a dictionary of product_id -> total_sales
        sales_results = {
            result.product_id: result.total_quantity 
            for result in self.db.exec(sales_query).all()
        }
        
        # Calculate days of stock for each product
        days_of_stock = {}
        for product_id in product_ids:
            product = product_map.get(product_id)
            if not product:
                continue
                
            # Get total sales or default to 0
            total_sales = sales_results.get(product_id, 0)
            
            # Calculate average daily sales (minimum of 0.1 to avoid division by zero)
            avg_daily_sales = max(0.1, total_sales / 30)
            
            # Calculate and round days of stock
            days_of_stock[product_id] = round(product.on_hand / avg_daily_sales, 1)
            
        return days_of_stock
    
    def calculate_reorder_point(self, product_id: UUID) -> int:
        """
        Calculate reorder point based on formula from PRD section 3.3:
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
        
        # Calculate average daily sales (minimum 0.1 to avoid issues with new products)
        avg_daily_sales = max(0.1, total_sales / 30)
        
        # Calculate reorder point (minimum of 1)
        reorder_point = max(1, product.safety_stock + round(avg_daily_sales * product.lead_time_days))
        
        return reorder_point
    
    def calculate_days_of_stock(self, product_id: UUID) -> float:
        """
        Calculate estimated days of stock remaining:
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
