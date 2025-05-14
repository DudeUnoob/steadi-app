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


CRON_SECRET_KEY = os.environ.get("CRON_SECRET_KEY")
CRON_API_KEY = os.environ.get("CRON_API_KEY")

def verify_cron_signature(request: Request):
   
    timestamp = int(time.time() / 60) * 60
    
    signature = request.headers.get("X-Cron-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing signature"
        )
    
    
    expected = hmac.new(
        CRON_SECRET_KEY.encode(),
        f"threshold_evaluator:{timestamp}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid signature"
        )
    
    return True

def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
   
    if not api_key or not hmac.compare_digest(api_key, CRON_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return True

async def run_threshold_evaluator_logic(db: Session) -> Dict[str, Any]:
   
    threshold_service = ThresholdService(db)
    start_time = time.time()
    
    
    results = threshold_service.evaluate_thresholds()
    
    
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
    
    return await run_threshold_evaluator_logic(db)

@router.post("/threshold-evaluator-simple", status_code=status.HTTP_200_OK)
async def run_threshold_evaluator_simple(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
   
    return await run_threshold_evaluator_logic(db) 