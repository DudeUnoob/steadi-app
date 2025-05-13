from uuid import UUID
from typing import Dict, List, Optional, Any
from sqlmodel import Session, select, func
from datetime import datetime, timedelta

from app.models.data_models.Product import Product
from app.models.data_models.Notification import Notification
from app.models.data_models.Supplier import Supplier
from app.models.enums.AlertLevel import AlertLevel
from app.models.enums.NotificationChannel import NotificationChannel
from app.models.service_classes.ThresholdService import ThresholdService

class AlertService:
    """Service for managing product inventory alerts"""
    
    def __init__(self, db: Session):
        self.db = db
        self.threshold_service = ThresholdService(db)
    
    def update_product_alert_levels(self, user_id: UUID) -> Dict[str, int]:
        """
        Update alert levels for all products according to the formula:
        - reorder_point = safety_stock + (avg_daily_sales × lead_time_days)
        - RED if on_hand <= reorder_point
        - YELLOW if on_hand <= reorder_point + safety_stock
        """
        products = self.db.exec(
            select(Product).where(Product.user_id == user_id)
        ).all()
        
        alert_counts = {
            "red": 0,
            "yellow": 0,
            "normal": 0,
            "total": len(products)
        }
        
        # Process products in batches to reduce database calls
        product_ids = [product.id for product in products]
        days_of_stock_map = self.threshold_service.calculate_batch_days_of_stock(product_ids)
        
        for product in products:
            old_alert_level = product.alert_level
            
            # Update reorder_point based on formula from PRD
            new_reorder_point = self.threshold_service.calculate_reorder_point(product.id)
            if product.reorder_point != new_reorder_point:
                product.reorder_point = new_reorder_point
                self.db.add(product)
            
            # Determine alert level according to PRD
            if product.on_hand <= product.reorder_point:
                new_alert_level = AlertLevel.RED
                alert_counts["red"] += 1
            elif product.on_hand <= (product.reorder_point + product.safety_stock):
                new_alert_level = AlertLevel.YELLOW
                alert_counts["yellow"] += 1
            else:
                new_alert_level = None
                alert_counts["normal"] += 1
            
            # Update product if alert level changed
            if old_alert_level != new_alert_level:
                product.alert_level = new_alert_level
                self.db.add(product)
                
                # Create notification if alert level is RED or YELLOW
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
        
        # Get days of stock for context
        days_of_stock = self.threshold_service.calculate_days_of_stock(product.id)
        
        if product.alert_level == AlertLevel.RED:
            message = f"URGENT: Reorder {max(1, product.reorder_point - product.on_hand)} × '{product.sku}' – Est. {days_of_stock} days left"
        else: 
            message = f"Reorder {max(1, product.reorder_point - product.on_hand)} × '{product.sku}' – Est. {days_of_stock} days left"
        
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
                "message": message,
                "days_of_stock": days_of_stock
            }
        )
        
        self.db.add(notification)
    
    def get_reorder_alerts(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all active reorder alerts for a user"""
      
        # Update alert levels before returning alerts
        self.update_product_alert_levels(user_id)
        
        products = self.db.exec(
            select(Product).where(
                (Product.user_id == user_id) &
                (Product.alert_level.in_([AlertLevel.RED, AlertLevel.YELLOW]))
            ).order_by(Product.alert_level, Product.name)
        ).all()
        
        # Get days of stock for all alert products in one batch query
        product_ids = [product.id for product in products]
        days_of_stock_map = self.threshold_service.calculate_batch_days_of_stock(product_ids)
        
        alerts = []
        for product in products:
            supplier_name = "Unknown Supplier"
            supplier_contact = None
            if product.supplier_id:
                supplier = self.db.get(Supplier, product.supplier_id)
                if supplier:
                    supplier_name = supplier.name
                    supplier_contact = supplier.contact_email
            
            days_of_stock = days_of_stock_map.get(product.id, 0)
            
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
                "needs_immediate_action": product.alert_level == AlertLevel.RED or days_of_stock < product.lead_time_days,
                "reorder_quantity": max(1, product.reorder_point - product.on_hand)
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
