from uuid import UUID
from typing import Dict, List, Optional, Any
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
import logging

from app.models.data_models.Product import Product
from app.models.data_models.Notification import Notification
from app.models.data_models.Supplier import Supplier
from app.models.data_models.User import User
from app.models.enums.AlertLevel import AlertLevel
from app.models.enums.NotificationChannel import NotificationChannel
from app.models.service_classes.ThresholdService import ThresholdService
from app.services.email_service import EmailService
from app.services.rate_limit_service import rate_limiter

logger = logging.getLogger(__name__)

class AlertService:
    """Service for managing product inventory alerts"""
    
    def __init__(self, db: Session):
        self.db = db
        self.threshold_service = ThresholdService(db)
        self.email_service = EmailService()
    
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
    
    def send_email_alerts(self, user_id: UUID) -> Dict[str, Any]:
        """
        Send email alerts for products that need reordering.
        Implements rate limiting as per PRD requirements.
        """
        # Check rate limit first
        tenant_id = str(user_id)  # Using user_id as tenant_id for now
        
        if not rate_limiter.check_rate_limit(tenant_id):
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return {
                "success": False,
                "message": "Rate limit exceeded. Please try again later.",
                "rate_limit_status": rate_limiter.get_rate_limit_status(tenant_id)
            }
        
        try:
            # Get user information
            user = self.db.get(User, user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return {"success": False, "message": "User not found"}
            
            # Get current alerts
            alerts = self.get_reorder_alerts(user_id)
            
            if not alerts:
                logger.info(f"No alerts to send for user {user_id}")
                return {"success": True, "message": "No alerts to send", "alerts_sent": 0}
            
            # Get alert counts
            alert_counts = self.update_product_alert_levels(user_id)
            
            # Send email
            email_sent = self.email_service.send_stock_alert_email(
                to_email=user.email,
                user_name=user.email.split('@')[0].title(),  # Simple name extraction
                alerts=alerts,
                alert_counts=alert_counts
            )
            
            if email_sent:
                # Create email notification record
                self._create_email_notification_record(user_id, alerts, alert_counts)
                
                logger.info(f"Email alert sent successfully to {user.email}")
                return {
                    "success": True,
                    "message": f"Email alert sent to {user.email}",
                    "alerts_sent": len(alerts),
                    "alert_counts": alert_counts
                }
            else:
                logger.error(f"Failed to send email alert to {user.email}")
                return {
                    "success": False,
                    "message": "Failed to send email alert",
                    "alerts_sent": 0
                }
                
        except Exception as e:
            logger.error(f"Error sending email alerts for user {user_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending email alerts: {str(e)}",
                "alerts_sent": 0
            }
    
    def _create_email_notification_record(
        self, 
        user_id: UUID, 
        alerts: List[Dict], 
        alert_counts: Dict[str, int]
    ) -> None:
        """Create a notification record for the email that was sent"""
        
        red_count = alert_counts.get("red", 0)
        yellow_count = alert_counts.get("yellow", 0)
        
        # Create summary message
        if red_count > 0:
            message = f"🚨 URGENT: {red_count} products need immediate reordering"
        elif yellow_count > 0:
            message = f"⚠️ {yellow_count} products approaching reorder point"
        else:
            message = "📊 Inventory status update sent"
        
        notification = Notification(
            user_id=user_id,
            channel=NotificationChannel.EMAIL,
            payload={
                "type": "stock_alert_email",
                "message": message,
                "alert_counts": alert_counts,
                "products_count": len(alerts),
                "red_alerts": red_count,
                "yellow_alerts": yellow_count,
                "email_sent_at": datetime.utcnow().isoformat()
            }
        )
        
        self.db.add(notification)
        self.db.commit()
    
    def get_rate_limit_status(self, user_id: UUID) -> Dict[str, Any]:
        """Get current rate limit status for a user"""
        tenant_id = str(user_id)
        return rate_limiter.get_rate_limit_status(tenant_id)
    
    def mark_all_notifications_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user. Returns count of updated notifications."""
        notifications = self.db.exec(
            select(Notification).where(
                (Notification.user_id == user_id) &
                (Notification.read_at == None)
            )
        ).all()
        
        count = 0
        for notification in notifications:
            notification.read_at = datetime.utcnow()
            self.db.add(notification)
            count += 1
        
        if count > 0:
            self.db.commit()
            logger.info(f"Marked {count} notifications as read for user {user_id}")
        
        return count
    
    def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """Delete a notification. Returns success status."""
        notification = self.db.exec(
            select(Notification).where(
                (Notification.id == notification_id) &
                (Notification.user_id == user_id)
            )
        ).first()
        
        if notification:
            self.db.delete(notification)
            self.db.commit()
            logger.info(f"Deleted notification {notification_id} for user {user_id}")
            return True
        
        return False
    
    def get_alert_summary(self, user_id: UUID) -> Dict[str, Any]:
        """Get a summary of current alerts and notification status"""
        # Update alert levels first
        alert_counts = self.update_product_alert_levels(user_id)
        
        # Get unread notification count
        unread_count = self.get_unread_notification_count(user_id)
        
        # Get rate limit status
        rate_limit_status = self.get_rate_limit_status(user_id)
        
        # Get recent alerts (last 24 hours)
        recent_alerts = self.db.exec(
            select(Notification).where(
                (Notification.user_id == user_id) &
                (Notification.sent_at >= datetime.utcnow() - timedelta(hours=24))
            ).order_by(Notification.sent_at.desc()).limit(10)
        ).all()
        
        return {
            "alert_counts": alert_counts,
            "unread_notifications": unread_count,
            "rate_limit_status": rate_limit_status,
            "recent_notifications": len(recent_alerts),
            "needs_immediate_attention": alert_counts.get("red", 0) > 0,
            "total_products_monitored": alert_counts.get("total", 0)
        }
