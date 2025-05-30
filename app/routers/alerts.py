from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import logging

from app.db.database import get_db
from app.models.data_models.User import User
from app.models.service_classes.AlertService import AlertService
from app.models.service_classes.ThresholdService import ThresholdService
from app.api.mvp.auth import get_current_user
from app.api.auth.supabase import get_current_supabase_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])

# Combined authentication dependency
async def get_authenticated_user(
    request: Request,
    token_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Combined authentication that works with both JWT tokens and Supabase tokens.
    First tries traditional JWT auth, and if that fails, tries Supabase auth.
    Returns the authenticated user or raises an authentication error.
    """
    # If traditional JWT auth worked, use that user
    if token_user:
        logger.info(f"User authenticated via JWT: {token_user.email}")
        return token_user
    
    try:
        # Try Supabase auth if JWT fails
        supabase_user = await get_current_supabase_user(request)
        supabase_id = supabase_user.get("id")
        
        if not supabase_id:
            logger.error("Supabase user has no ID")
            raise HTTPException(status_code=401, detail="Invalid Supabase user information")
        
        # Find user by Supabase ID
        user = db.exec(select(User).where(User.supabase_id == supabase_id)).first()
        
        if not user:
            # This shouldn't happen if the sync endpoint is working properly
            logger.error(f"No user found for Supabase ID: {supabase_id}")
            raise HTTPException(status_code=401, detail="User not found in system")
        
        logger.info(f"User authenticated via Supabase: {user.email}")
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Not authenticated")

@router.get("/reorder", response_model=List[Dict[str, Any]])
async def get_reorder_alerts(
    request: Request,
    current_user: User = Depends(get_authenticated_user),
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
    request: Request,
    current_user: User = Depends(get_authenticated_user),
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

@router.post("/evaluate-thresholds")
async def evaluate_thresholds(
    request: Request,
    product_id: Optional[UUID] = None,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger threshold evaluation to recalculate reorder points and alert levels.
    Can be run for a specific product or all products.
    
    - Formula: reorder_point = safety_stock + (avg_daily_sales × lead_time_days)
    - Alert Levels: 
      - RED if on_hand <= reorder_point
      - YELLOW if on_hand <= reorder_point + safety_stock
    """
    threshold_service = ThresholdService(db)
    results = threshold_service.evaluate_thresholds(product_id)
    
    
    alert_service = AlertService(db)
    alert_counts = alert_service.update_product_alert_levels(current_user.id)
    
    return {
        "message": f"Evaluated thresholds for {len(results)} products",
        "updated_products": results,
        "alert_counts": alert_counts
    }

@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_notifications(
    request: Request,
    include_read: bool = Query(False, description="Include notifications that have been read"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications to return"),
    current_user: User = Depends(get_authenticated_user),
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
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications for the current user"""
    alert_service = AlertService(db)
    count = alert_service.get_unread_notification_count(current_user.id)
    return {"unread_count": count}

@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    request: Request,
    notification_id: UUID,
    current_user: User = Depends(get_authenticated_user),
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

@router.post("/send-email")
async def send_email_alerts(
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Send email alerts for products that need reordering"""
    alert_service = AlertService(db)
    result = alert_service.send_email_alerts(current_user.id)
    
    if not result["success"]:
        if "rate limit" in result["message"].lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
    
    return result

@router.get("/summary")
async def get_alert_summary(
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive alert summary including counts, notifications, and rate limits"""
    alert_service = AlertService(db)
    summary = alert_service.get_alert_summary(current_user.id)
    return summary

@router.get("/rate-limit-status")
async def get_rate_limit_status(
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get current rate limit status for the user"""
    alert_service = AlertService(db)
    status_info = alert_service.get_rate_limit_status(current_user.id)
    return status_info

@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for the current user"""
    alert_service = AlertService(db)
    count = alert_service.mark_all_notifications_read(current_user.id)
    return {"success": True, "message": f"Marked {count} notifications as read", "count": count}

@router.delete("/notifications/{notification_id}")
async def delete_notification(
    request: Request,
    notification_id: UUID,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Delete a notification"""
    alert_service = AlertService(db)
    success = alert_service.delete_notification(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or you don't have permission to delete it"
        )
    
    return {"success": True, "message": "Notification deleted"} 