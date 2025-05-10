import os
from sqlmodel import Session
from sqlalchemy import text, inspect
from app.db.database import engine
from dotenv import load_dotenv
import time


load_dotenv()

def fix_schema():
    """
    Fix the database schema by creating any missing tables
    """
    
    inspector = inspect(engine)
    
  
    existing_tables = set(inspector.get_table_names())
    print(f"Existing tables: {existing_tables}")
    
    
    required_tables = {
        'user', 'supplier', 'product', 'sale', 'inventoryledger', 
        'purchaseorder', 'purchaseorderitem', 'notification', 'skualias'
    }
    
    
    missing_tables = required_tables - existing_tables
    print(f"Missing tables: {missing_tables}")
    
    if not missing_tables:
        print("All required tables exist. No action needed.")
        return
    
   
    print("Creating missing tables...")
    
   
    from sqlmodel import SQLModel
    from app.models.data_models.User import User
    from app.models.data_models.Supplier import Supplier
    
    from app.models.data_models.SkuAlias import SkuAlias
    from app.models.data_models.Product import Product
    from app.models.data_models.Sale import Sale
    from app.models.data_models.InventoryLedger import InventoryLedger
    from app.models.data_models.PurchaseOrder import PurchaseOrder
    from app.models.data_models.PurchaseOrderItem import PurchaseOrderItem
    from app.models.data_models.Notification import Notification
    
   
    SQLModel.metadata.create_all(engine)
    
   
    inspector = inspect(engine)
    new_existing_tables = set(inspector.get_table_names())
    still_missing = required_tables - new_existing_tables
    
    if still_missing:
        print(f"Warning: Some tables are still missing: {still_missing}")
    else:
        print("All required tables have been successfully created!")

if __name__ == "__main__":
    fix_schema() 