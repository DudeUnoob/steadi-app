from uuid import UUID
from typing import Dict, List, Optional, Any
from sqlmodel import Session, select, func
from datetime import datetime, timedelta

from app.models.data_models.Product import Product
from app.models.data_models.Notification import Notification
from app.models.data_models.Supplier import Supplier
from app.models.enums.AlertLevel import AlertLevel
from app.models.enums.NotificationChannel import NotificationChannel

class AlertService:
    """Service for managing product inventory alerts"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_product_alert_levels(self, user_id: UUID) -> Dict[str, int]:
       
        
        products = self.db.exec(
            select(Product).where(Product.user_id == user_id)
        ).all()
        
       
        alert_counts = {
            "red": 0,
            "yellow": 0,
            "normal": 0,
            "total": len(products)
        }
        
        
        for product in products:
            old_alert_level = product.alert_level
            
            
            if product.on_hand <= product.safety_stock:
                new_alert_level = AlertLevel.RED
                alert_counts["red"] += 1
            elif product.on_hand <= product.reorder_point:
                new_alert_level = AlertLevel.YELLOW
                alert_counts["yellow"] += 1
            else:
                new_alert_level = None
                alert_counts["normal"] += 1
            
           
            if old_alert_level != new_alert_level:
                product.alert_level = new_alert_level
                self.db.add(product)
                
                
                if new_alert_level in [AlertLevel.RED, AlertLevel.YELLOW]:
                    self._create_reorder_notification(product, user_id)
        
        self.db.commit()
        return alert_counts
    
    def _create_reorder_notification(self, product: Product, user_id: UUID) -> None:
        """Create a notification for a product that needs reordering"""
        
        supplier_name = "Unknown Supplier"
        if product.supplier_id:
            supplier = self.db.get(Supplier, product.supplier_id)
            if supplier:
                supplier_name = supplier.name
        
        
        if product.alert_level == AlertLevel.RED:
            message = f"URGENT: {product.name} (SKU: {product.sku}) is below safety stock level! Current stock: {product.on_hand}"
        else: 
            message = f"{product.name} (SKU: {product.sku}) has reached reorder point. Current stock: {product.on_hand}"
        
        
        notification = Notification(
            user_id=user_id,
            channel=NotificationChannel.IN_APP,
            payload={
                "product_id": str(product.id),
                "product_name": product.name,
                "sku": product.sku,
                "on_hand": product.on_hand,
                "reorder_point": product.reorder_point,
                "safety_stock": product.safety_stock,
                "alert_level": product.alert_level,
                "supplier_name": supplier_name,
                "supplier_id": str(product.supplier_id) if product.supplier_id else None,
                "message": message
            }
        )
        
        self.db.add(notification)
    
    def get_reorder_alerts(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all active reorder alerts for a user"""
      
        self.update_product_alert_levels(user_id)
        
        
        products = self.db.exec(
            select(Product).where(
                (Product.user_id == user_id) &
                (Product.alert_level.in_([AlertLevel.RED, AlertLevel.YELLOW]))
            ).order_by(Product.alert_level, Product.name)
        ).all()
        
        
        alerts = []
        for product in products:
            
            supplier_name = "Unknown Supplier"
            supplier_contact = None
            if product.supplier_id:
                supplier = self.db.get(Supplier, product.supplier_id)
                if supplier:
                    supplier_name = supplier.name
                    supplier_contact = supplier.contact_email
            
            
            days_of_stock = 0
            if product.on_hand > 0:
                
                from sqlalchemy.sql import text
                daily_sales_query = text("""
                    SELECT COALESCE(AVG(quantity), 0) as avg_daily_sales
                    FROM sale
                    WHERE product_id = :product_id
                    AND sale_date >= :start_date
                    AND user_id = :user_id
                """)
                
                result = self.db.execute(
                    daily_sales_query,
                    {
                        "product_id": str(product.id),
                        "start_date": datetime.utcnow() - timedelta(days=30),
                        "user_id": str(user_id)
                    }
                ).first()
                
                avg_daily_sales = result[0] if result and result[0] > 0 else 0.1  # Avoid division by zero
                days_of_stock = round(product.on_hand / avg_daily_sales)
            
            
            alerts.append({
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "on_hand": product.on_hand,
                "reorder_point": product.reorder_point,
                "safety_stock": product.safety_stock,
                "alert_level": product.alert_level,
                "supplier_name": supplier_name,
                "supplier_contact": supplier_contact,
                "supplier_id": str(product.supplier_id) if product.supplier_id else None,
                "days_of_stock": days_of_stock,
                "lead_time_days": product.lead_time_days,
                "needs_immediate_action": product.alert_level == AlertLevel.RED or days_of_stock < product.lead_time_days
            })
        
        return alerts
    
    def get_unread_notification_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user"""
        result = self.db.exec(
            select(func.count(Notification.id)).where(
                (Notification.user_id == user_id) &
                (Notification.read_at == None)
            )
        ).one()
        
        return result
    
    def mark_notification_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read. Returns success status."""
        notification = self.db.exec(
            select(Notification).where(
                (Notification.id == notification_id) &
                (Notification.user_id == user_id)
            )
        ).first()
        
        if notification:
            notification.read_at = datetime.utcnow()
            self.db.add(notification)
            self.db.commit()
            return True
        
        return False
    
    def get_user_notifications(self, user_id: UUID, include_read: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if not include_read:
            query = query.where(Notification.read_at == None)
            
        query = query.order_by(Notification.sent_at.desc()).limit(limit)
        
        notifications = self.db.exec(query).all()
        
       
        result = []
        for notif in notifications:
            result.append({
                "id": str(notif.id),
                "channel": notif.channel,
                "payload": notif.payload,
                "sent_at": notif.sent_at,
                "read_at": notif.read_at
            })
            
        return result
