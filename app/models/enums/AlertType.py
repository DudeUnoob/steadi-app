from enum import Enum

class AlertType(str, Enum):
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    REORDER_POINT = "REORDER_POINT"
    EXPIRY_WARNING = "EXPIRY_WARNING"
    SUPPLIER_ISSUE = "SUPPLIER_ISSUE"
    PRICE_CHANGE = "PRICE_CHANGE"
    SYSTEM_ERROR = "SYSTEM_ERROR" 