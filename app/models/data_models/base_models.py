"""Base model classes without cross-dependencies"""
from sqlmodel import SQLModel
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, List
from sqlmodel import Field

# This file only contains common model definitions or mixins
# No circular dependencies should exist here

class TimestampMixin:
    """Mixin to add creation and update timestamps"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

__all__ = ["TimestampMixin"] 