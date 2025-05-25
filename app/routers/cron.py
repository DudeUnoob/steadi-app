from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from sqlmodel import Session, select
from typing import Dict, List, Any, Optional
import hmac
import hashlib
import os
import time
from datetime import datetime

from app.db.database import get_db
from app.models.service_classes.ThresholdService import ThresholdService
from app.models.data_models.Connector import Connector
from app.models.enums.ConnectorProvider import ConnectorProvider
from app.services.connector_service import ConnectorService

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

async def run_pos_sync_logic(db: Session) -> Dict[str, Any]:
    """
    Automated POS connector synchronization logic that runs every 15 minutes.
    Syncs all ACTIVE connectors and updates their status.
    """
    connector_service = ConnectorService(db)
    start_time = time.time()
    
    # Get all active POS connectors (exclude CSV)
    active_connectors = db.exec(
        select(Connector).where(
            Connector.status == "ACTIVE",
            Connector.provider.in_([
                ConnectorProvider.SHOPIFY,
                ConnectorProvider.SQUARE, 
                ConnectorProvider.LIGHTSPEED
            ])
        )
    ).all()
    
    sync_results = []
    total_items_synced = 0
    total_errors = 0
    
    for connector in active_connectors:
        try:
            # Sync based on provider type
            if connector.provider == ConnectorProvider.SHOPIFY:
                result = await connector_service.sync_shopify(connector.id)
            elif connector.provider == ConnectorProvider.SQUARE:
                result = await connector_service.sync_square(connector.id)
            elif connector.provider == ConnectorProvider.LIGHTSPEED:
                result = await connector_service.sync_lightspeed(connector.id)
            else:
                continue
            
            sync_results.append({
                "connector_id": str(connector.id),
                "provider": connector.provider.value,
                "status": result.status,
                "items_synced": result.items_synced,
                "items_updated": result.items_updated,
                "items_created": result.items_created,
                "errors": result.errors
            })
            
            total_items_synced += result.items_synced
            total_errors += len(result.errors)
            
        except Exception as e:
            # Log the error and mark connector as having issues
            error_msg = str(e)
            sync_results.append({
                "connector_id": str(connector.id),
                "provider": connector.provider.value,
                "status": "ERROR",
                "items_synced": 0,
                "items_updated": 0,
                "items_created": 0,
                "errors": [error_msg]
            })
            total_errors += 1
            
            # Update connector status to ERROR
            connector.status = "ERROR"
            db.add(connector)
    
    # Commit any connector status updates
    db.commit()
    
    # After syncing, run threshold evaluator on all updated products
    # This ensures alerts are fresh after inventory updates
    threshold_service = ThresholdService(db)
    threshold_results = threshold_service.evaluate_thresholds()
    
    execution_time = time.time() - start_time
    execution_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "execution_time_seconds": round(execution_time, 3),
        "connectors_processed": len(active_connectors),
        "total_items_synced": total_items_synced,
        "total_errors": total_errors,
        "sync_results": sync_results,
        "threshold_evaluation": {
            "products_processed": len(threshold_results),
            "alert_counts": {
                "red": len([r for r in threshold_results if r["alert_level"] == "RED"]),
                "yellow": len([r for r in threshold_results if r["alert_level"] == "YELLOW"]),
                "normal": len([r for r in threshold_results if r["alert_level"] is None])
            }
        }
    }
    
    return {
        "status": "success" if total_errors == 0 else "partial_success",
        "message": f"POS sync completed at {datetime.utcnow().isoformat()}. Processed {len(active_connectors)} connectors.",
        "execution_info": execution_log
    }

@router.post("/pos-sync", status_code=status.HTTP_200_OK)
async def run_pos_sync(
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_cron_signature)
):
    """
    Automated POS connector synchronization endpoint.
    Designed to be called every 15 minutes by EventBridge scheduler.
    """
    return await run_pos_sync_logic(db)

@router.post("/pos-sync-simple", status_code=status.HTTP_200_OK)
async def run_pos_sync_simple(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """
    Simple POS sync endpoint for testing and manual triggers.
    Uses API key authentication instead of signature verification.
    """
    return await run_pos_sync_logic(db) 