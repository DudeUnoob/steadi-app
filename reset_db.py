import os
from sqlmodel import Session
from sqlalchemy import text, inspect
from app.db.database import engine
from dotenv import load_dotenv
import time


load_dotenv()

def reset_database():
    """
    Reset the database by dropping all tables and recreating them
    """
    with Session(engine) as session:
        print("Dropping all tables...")
        
        try:
            
            session.exec(text("DROP TABLE IF EXISTS product CASCADE;"))
            session.exec(text("DROP TABLE IF EXISTS supplier CASCADE;"))
            session.exec(text("DROP TABLE IF EXISTS user_table CASCADE;"))
            session.exec(text("DROP TABLE IF EXISTS sale CASCADE;"))
            session.exec(text("DROP TABLE IF EXISTS inventoryledger CASCADE;"))
            session.exec(text("DROP TABLE IF EXISTS purchaseorderitem CASCADE;"))
            session.exec(text("DROP TABLE IF EXISTS purchaseorder CASCADE;"))
            session.exec(text("DROP TABLE IF EXISTS notification CASCADE;"))
            session.exec(text("DROP TABLE IF EXISTS skualias CASCADE;"))
            
            session.commit()
        except Exception as e:
            print(f"Error dropping tables: {str(e)}")
            session.rollback()
    
    
    time.sleep(1)
    
    print("Creating tables with new schema...")
    
   
    try:
        
        from sqlmodel import SQLModel
        
       
        from app.models.data_models.User import User
        from app.models.data_models.Supplier import Supplier
        
        
        from app.models.data_models.Product import Product
        
       
        from app.models.data_models.Sale import Sale
        from app.models.data_models.InventoryLedger import InventoryLedger
        from app.models.data_models.PurchaseOrder import PurchaseOrder
        from app.models.data_models.PurchaseOrderItem import PurchaseOrderItem
        from app.models.data_models.Notification import Notification
        from app.models.data_models.SkuAlias import SkuAlias
        
        
        SQLModel.metadata.create_all(engine)
        print("Database reset successfully!")
    except Exception as e:
        print(f"Error creating tables: {str(e)}")

if __name__ == "__main__":
    reset_database() 