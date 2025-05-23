from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from app.models.enums.ConnectorProvider import ConnectorProvider

class ConnectorCreate(BaseModel):
    provider: ConnectorProvider
    config: Dict[str, Any]

class ConnectorUpdate(BaseModel):
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class ConnectorRead(BaseModel):
    id: UUID
    provider: ConnectorProvider
    status: str
    created_by: UUID
    last_sync: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    config: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class ConnectorSync(BaseModel):
    connector_id: UUID
    provider: ConnectorProvider
    status: str
    items_synced: int
    items_updated: int
    items_created: int
    sync_started_at: datetime
    sync_completed_at: Optional[datetime] = None
    errors: List[str] = []

class CSVUploadMapping(BaseModel):
    sku_column: str
    name_column: str
    on_hand_column: str
    cost_column: Optional[str] = None
    supplier_name_column: Optional[str] = None
    variant_column: Optional[str] = None

class CSVUploadResponse(BaseModel):
    imported_items: int
    updated_items: int
    created_items: int
    errors: List[str] = []
    warnings: List[str] = []
    
    # Enhanced reporting fields
    total_rows_processed: int = 0
    skus_processed: List[str] = []
    suppliers_created: int = 0
    alerts_generated: int = 0
    threshold_updates: int = 0
    
    # Summary for success banner
    success_message: str = ""
    
    # Optional link data for inventory filtering
    filter_params: Optional[Dict[str, Any]] = None

class ConnectorTestResponse(BaseModel):
    provider: ConnectorProvider
    status: str
    connection_valid: bool
    test_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None 