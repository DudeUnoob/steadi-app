"""Data models initialization in the correct order to avoid circular imports"""

# First, import all enum types
from app.models.enums.AlertLevel import AlertLevel
from app.models.enums.NotificationChannel import NotificationChannel
from app.models.enums.POStatus import POStatus
from app.models.enums.UserRole import UserRole

# Base models without relationships to other models
from app.models.data_models.base_models import *

# Then import the models in dependency order
from app.models.data_models.Supplier import Supplier
from app.models.data_models.Product import Product
from app.models.data_models.User import User
from app.models.data_models.Notification import Notification
from app.models.data_models.InventoryLedger import InventoryLedger
from app.models.data_models.Sale import Sale
from app.models.data_models.PurchaseOrder import PurchaseOrder
from app.models.data_models.PurchaseOrderItem import PurchaseOrderItem

# List all models for easy access
__all__ = [
    "Supplier",
    "Product",
    "User",
    "Notification",
    "InventoryLedger",
    "Sale", 
    "PurchaseOrder",
    "PurchaseOrderItem"
] 