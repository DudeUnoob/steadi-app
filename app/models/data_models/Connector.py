from app.models.enums.ConnectorProvider import ConnectorProvider
from sqlmodel import Field, SQLModel, JSON, Column
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any

class Connector(SQLModel, table=True):
    """Integration with external POS/inventory systems"""
    
    id: Optional[UUID] = Field(default=None, primary_key=True)
    provider: ConnectorProvider
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    status: str = Field(default="PENDING")
    created_by: UUID = Field(foreign_key="user.id")
    last_sync: Optional[datetime] = None
    config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
