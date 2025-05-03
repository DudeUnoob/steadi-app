from typing import Optional, Dict, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from uuid import UUID, uuid4
from app.models.enums.NotificationChannel import NotificationChannel
from sqlalchemy import JSON, Column

if TYPE_CHECKING:
    from app.models.data_models.User import User

class Notification(SQLModel, table=True):
    """User notifications for alerts and events"""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    channel: NotificationChannel
    payload: Optional[Dict] = Field(default={}, sa_column=Column(JSON))
    sent_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    # Relationships
    user: "User" = Relationship(back_populates="notifications")
