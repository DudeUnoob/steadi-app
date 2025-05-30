from enum import Enum

class AuditAction(str, Enum):
    # User actions
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    
    # Product actions
    PRODUCT_CREATED = "PRODUCT_CREATED"
    PRODUCT_UPDATED = "PRODUCT_UPDATED"
    PRODUCT_DELETED = "PRODUCT_DELETED"
    
    # Inventory actions
    INVENTORY_ADJUSTED = "INVENTORY_ADJUSTED"
    CSV_IMPORT = "CSV_IMPORT"
    POS_SYNC = "POS_SYNC"
    
    # Supplier actions
    SUPPLIER_CREATED = "SUPPLIER_CREATED"
    SUPPLIER_UPDATED = "SUPPLIER_UPDATED"
    SUPPLIER_DELETED = "SUPPLIER_DELETED"
    
    # Connector actions
    CONNECTOR_CREATED = "CONNECTOR_CREATED"
    CONNECTOR_UPDATED = "CONNECTOR_UPDATED"
    CONNECTOR_DELETED = "CONNECTOR_DELETED"
    CONNECTOR_SYNCED = "CONNECTOR_SYNCED"
    
    # Alert actions
    ALERT_CREATED = "ALERT_CREATED"
    ALERT_RESOLVED = "ALERT_RESOLVED"
    ALERT_DISMISSED = "ALERT_DISMISSED"
    
    # System actions
    SYSTEM_BACKUP = "SYSTEM_BACKUP"
    SYSTEM_RESTORE = "SYSTEM_RESTORE"
    SYSTEM_ERROR = "SYSTEM_ERROR" 