from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from sqlmodel import Session
from typing import Dict, List, Any, Optional
import hmac
import hashlib
import os
import time
from datetime import datetime

from app.db.database import get_db
from app.models.service_classes.ThresholdService import ThresholdService

router = APIRouter(prefix="/cron", tags=["cron"])

# Secret keys for secure cron invocation
CRON_SECRET_KEY = os.environ.get("CRON_SECRET_KEY", "default-secret-replace-in-production")
CRON_API_KEY = os.environ.get("CRON_API_KEY", "default-api-key-replace-in-production")

def verify_cron_signature(request: Request):
    """
    Verify the request is coming from an authorized cron service
    using a simple HMAC-based authentication mechanism.
    """
    # Get current timestamp (rounded to nearest minute)
    timestamp = int(time.time() / 60) * 60
    
    # Get the signature from header
    signature = request.headers.get("X-Cron-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing signature"
        )
    
    # Calculate expected signature
    expected = hmac.new(
        CRON_SECRET_KEY.encode(),
        f"threshold_evaluator:{timestamp}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Check if signatures match
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid signature"
        )
    
    return True

def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    """
    Simpler alternative to verify_cron_signature.
    Verifies the request using a static API key.
    """
    if not api_key or not hmac.compare_digest(api_key, CRON_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return True

async def run_threshold_evaluator_logic(db: Session) -> Dict[str, Any]:
    """
    Shared logic for both threshold evaluator endpoints.
    """
    threshold_service = ThresholdService(db)
    start_time = time.time()
    
    # Process all products (no specific product_id)
    results = threshold_service.evaluate_thresholds()
    
    # Log execution information
    execution_time = time.time() - start_time
    execution_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "execution_time_seconds": round(execution_time, 3),
        "products_processed": len(results),
        "alert_counts": {
            "red": len([r for r in results if r["alert_level"] == "RED"]),
            "yellow": len([r for r in results if r["alert_level"] == "YELLOW"]),
            "normal": len([r for r in results if r["alert_level"] is None])
        }
    }
    
    return {
        "status": "success",
        "message": f"Threshold evaluator completed successfully at {datetime.utcnow().isoformat()}",
        "execution_info": execution_log
    }

@router.post("/threshold-evaluator", status_code=status.HTTP_200_OK)
async def run_threshold_evaluator(
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_cron_signature)
):
    """
    Run the Automated Stock-Threshold Engine as specified in PRD section 3.3.
    This endpoint is designed to be called by an external cron service (e.g., cron-job.org) 
    every 15 minutes as specified in the PRD.
    
    Security:
    - Requires a valid signature in the X-Cron-Signature header
    
    Implementation:
    - Evaluates all product thresholds using the formula:
      reorder_point = safety_stock + (avg_daily_sales × lead_time_days)
    - Updates alert levels for each product
    """
    return await run_threshold_evaluator_logic(db)

@router.post("/threshold-evaluator-simple", status_code=status.HTTP_200_OK)
async def run_threshold_evaluator_simple(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """
    Simplified version of the threshold evaluator endpoint that uses a static API key
    instead of a time-based signature. This is easier to set up with services like cron-job.org.
    
    Security:
    - Requires a valid API key in the X-API-Key header
    
    Implementation:
    - Same as the regular threshold evaluator endpoint
    """
    return await run_threshold_evaluator_logic(db) 