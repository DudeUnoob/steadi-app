from uuid import UUID
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlmodel import Session, select, func
from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale

class AnalyticsService:
    """Computes and caches business analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_turnover_rate(self, product_id: Optional[UUID] = None, period: int = 30) -> Dict:
        """Calculate inventory turnover rate"""
        start_date = datetime.utcnow() - timedelta(days=period)
        
        # Get cost of goods sold
        sales_query = select(
            func.sum(Sale.quantity * Product.cost)
        ).join(Product).where(
            Sale.sale_date >= start_date
        )
        if product_id:
            sales_query = sales_query.where(Product.id == product_id)
        cost_of_goods_sold = self.db.exec(sales_query).first() or 0
        
        # Get average inventory value
        inventory_query = select(
            func.avg(Product.on_hand * Product.cost)
        )
        if product_id:
            inventory_query = inventory_query.where(Product.id == product_id)
        avg_inventory_value = self.db.exec(inventory_query).first() or 0
        
        turnover_rate = cost_of_goods_sold / avg_inventory_value if avg_inventory_value > 0 else 0
        
        return {
            "turnover_rate": turnover_rate,
            "period_days": period,
            "cost_of_goods_sold": cost_of_goods_sold,
            "avg_inventory_value": avg_inventory_value
        }
    
    def get_top_sellers(self, limit: int = 10, period: int = 30) -> List[Dict]:
        """Get top selling products"""
        start_date = datetime.utcnow() - timedelta(days=period)
        
        query = select(
            Product.sku,
            Product.name,
            func.sum(Sale.quantity).label('total_sold')
        ).join(
            Sale
        ).where(
            Sale.sale_date >= start_date
        ).group_by(
            Product.id
        ).order_by(
            func.sum(Sale.quantity).desc()
        ).limit(limit)
        
        results = self.db.exec(query).all()
        
        return [
            {
                "sku": r.sku,
                "name": r.name,
                "total_sold": r.total_sold
            }
            for r in results
        ]
    
    def get_sales_history(self, product_id: UUID, period: int = 7) -> List[Dict]:
        """Get sales history for product"""
        start_date = datetime.utcnow() - timedelta(days=period)
        
        query = select(
            func.date_trunc('day', Sale.sale_date).label('date'),
            func.sum(Sale.quantity).label('quantity')
        ).where(
            Sale.product_id == product_id,
            Sale.sale_date >= start_date
        ).group_by(
            func.date_trunc('day', Sale.sale_date)
        ).order_by(
            func.date_trunc('day', Sale.sale_date)
        )
        
        results = self.db.exec(query).all()
        
        # Create a complete timeline with zeros for days without sales
        timeline = []
        for i in range(period):
            date = start_date + timedelta(days=i)
            timeline.append({
                "date": date.date(),
                "quantity": 0
            })
            
        # Fill in actual sales data
        for result in results:
            for day in timeline:
                if day["date"] == result.date.date():
                    day["quantity"] = result.quantity
                    break
                    
        return timeline
