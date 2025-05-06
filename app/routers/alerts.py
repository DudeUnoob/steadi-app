from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from app.db.database import get_db
from app.models.data_models.User import User
from app.models.service_classes.AlertService import AlertService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/reorder", response_model=List[Dict[str, Any]])
async def get_reorder_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all products that need reordering based on inventory levels.
    This includes:
    - Products with RED alert level (below safety stock)
    - Products with YELLOW alert level (below reorder point)
    """
    alert_service = AlertService(db)
    alerts = alert_service.get_reorder_alerts(current_user.id)
    return alerts

@router.get("/count")
async def get_alert_counts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get counts of products at each alert level:
    - RED: below safety stock
    - YELLOW: below reorder point but above safety stock
    - Normal: above reorder point
    """
    alert_service = AlertService(db)
    counts = alert_service.update_product_alert_levels(current_user.id)
    return counts

@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_notifications(
    include_read: bool = Query(False, description="Include notifications that have been read"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notifications for the current user.
    By default, only unread notifications are returned.
    """
    alert_service = AlertService(db)
    notifications = alert_service.get_user_notifications(
        user_id=current_user.id,
        include_read=include_read,
        limit=limit
    )
    return notifications

@router.get("/notifications/unread-count")
async def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications for the current user"""
    alert_service = AlertService(db)
    count = alert_service.get_unread_notification_count(current_user.id)
    return {"unread_count": count}

@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    alert_service = AlertService(db)
    success = alert_service.mark_notification_read(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or you don't have permission to access it"
        )
    
    return {"success": True, "message": "Notification marked as read"} 