from typing import List, Dict, Optional, Any
from sqlmodel import Session, select, func
from uuid import UUID
from datetime import datetime, timedelta
from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale

class AnalyticsService:
    """Computes and caches business analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_turnover_rate(self, product_id: Optional[UUID] = None, period: int = 30) -> Dict[str, Any]:
        """Calculate inventory turnover rate
        turnover_rate = cost_of_goods_sold ÷ avg_inventory_value
        """
        # Define date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period)
        
        # Base query for cost of goods sold
        if product_id:
            # For a specific product
            products = [self.db.exec(select(Product).where(Product.id == product_id)).first()]
            if not products[0]:
                raise ValueError(f"Product with ID {product_id} not found")
                
            # Get sales for the period
            sales_query = select(
                Sale.product_id,
                func.sum(Sale.quantity).label("total_quantity")
            ).where(
                (Sale.product_id == product_id) &
                (Sale.sale_date >= start_date) &
                (Sale.sale_date <= end_date)
            ).group_by(Sale.product_id)
            
        else:
            # For all products
            products = self.db.exec(select(Product)).all()
            
            # Get sales for all products in the period
            sales_query = select(
                Sale.product_id,
                func.sum(Sale.quantity).label("total_quantity")
            ).where(
                (Sale.sale_date >= start_date) &
                (Sale.sale_date <= end_date)
            ).group_by(Sale.product_id)
        
        # Execute sales query
        sales_results = {
            sale.product_id: sale.total_quantity 
            for sale in self.db.exec(sales_query).all()
        }
        
        # Calculate metrics
        total_cost_of_goods_sold = 0
        total_inventory_value = 0
        turnover_rates = {}
        
        for product in products:
            # Get sales quantity
            sales_quantity = sales_results.get(product.id, 0)
            
            # Calculate cost of goods sold
            cost_of_goods_sold = sales_quantity * product.cost
            
            # Inventory value (current)
            inventory_value = product.on_hand * product.cost
            
            # Calculate turnover rate
            if inventory_value > 0:
                turnover_rate = cost_of_goods_sold / inventory_value
            else:
                turnover_rate = 0
                
            # Add to totals
            total_cost_of_goods_sold += cost_of_goods_sold
            total_inventory_value += inventory_value
            
            # Store individual turnover rate
            turnover_rates[str(product.id)] = {
                "sku": product.sku,
                "name": product.name,
                "turnover_rate": round(turnover_rate, 2),
                "cost_of_goods_sold": round(cost_of_goods_sold, 2),
                "inventory_value": round(inventory_value, 2)
            }
        
        # Calculate overall turnover rate
        overall_turnover_rate = 0
        if total_inventory_value > 0:
            overall_turnover_rate = total_cost_of_goods_sold / total_inventory_value
            
        return {
            "overall_turnover_rate": round(overall_turnover_rate, 2),
            "total_cost_of_goods_sold": round(total_cost_of_goods_sold, 2),
            "total_inventory_value": round(total_inventory_value, 2),
            "period_days": period,
            "products": turnover_rates
        }
    
    def get_top_sellers(self, limit: int = 10, period: int = 30) -> List[Dict[str, Any]]:
        """Get top selling products"""
        # Define date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period)
        
        # Query to get top selling products
        query = select(
            Sale.product_id,
            func.sum(Sale.quantity).label("total_quantity")
        ).where(
            (Sale.sale_date >= start_date) &
            (Sale.sale_date <= end_date)
        ).group_by(
            Sale.product_id
        ).order_by(
            func.sum(Sale.quantity).desc()
        ).limit(limit)
        
        # Execute query
        results = self.db.exec(query).all()
        
        # Format results with product details
        top_sellers = []
        for result in results:
            product = self.db.exec(select(Product).where(Product.id == result.product_id)).first()
            if product:
                top_sellers.append({
                    "product_id": str(product.id),
                    "sku": product.sku,
                    "name": product.name,
                    "quantity_sold": result.total_quantity,
                    "revenue": round(result.total_quantity * product.cost, 2)
                })
        
        return top_sellers
    
    def get_sales_history(self, product_id: UUID, period: int = 7) -> List[Dict[str, Any]]:
        """Get sales history for product"""
        # Define date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period)
        
        # Verify product exists
        product = self.db.exec(select(Product).where(Product.id == product_id)).first()
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Prepare result structure (initialize with zero sales for all days)
        sales_history = []
        for i in range(period):
            date = end_date - timedelta(days=i)
            sales_history.append({
                "date": date.strftime("%Y-%m-%d"),
                "quantity": 0
            })
        
        # Query to get daily sales for the period
        query = select(
            func.date_trunc('day', Sale.sale_date).label("day"),
            func.sum(Sale.quantity).label("total_quantity")
        ).where(
            (Sale.product_id == product_id) &
            (Sale.sale_date >= start_date) &
            (Sale.sale_date <= end_date)
        ).group_by(
            func.date_trunc('day', Sale.sale_date)
        )
        
        # Execute query
        results = self.db.exec(query).all()
        
        # Map results to the sales history
        for result in results:
            date_str = result.day.strftime("%Y-%m-%d")
            for entry in sales_history:
                if entry["date"] == date_str:
                    entry["quantity"] = result.total_quantity
                    break
        
        # Reverse to get chronological order
        sales_history.reverse()
        
        return sales_history
