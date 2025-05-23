#!/usr/bin/env python3
"""
Script to drop duplicate tables that were created with plural names.
This script will drop the plural-named tables (users, suppliers, products, etc.)
and keep the original singular-named tables (user, supplier, product, etc.)
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def drop_duplicate_tables():
    """Drop duplicate tables with plural names"""
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    engine = create_engine(DATABASE_URL)
    
    # List of duplicate tables to drop (plural names)
    duplicate_tables = [
        "users",
        "suppliers", 
        "products",
        "sales",
        "alerts",
        "notifications",
        "connectors",
        "audit_logs",
        "permissions",
        "role_permissions",
        "inventory_ledger",
        "purchase_orders",
        "purchase_order_items",
        "sku_aliases"
    ]
    
    with engine.connect() as conn:
        # Get list of existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print("Existing tables:", existing_tables)
        print("\nDropping duplicate tables...")
        
        for table_name in duplicate_tables:
            if table_name in existing_tables:
                try:
                    # Drop the table
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    print(f"✓ Dropped table: {table_name}")
                except Exception as e:
                    print(f"✗ Failed to drop table {table_name}: {e}")
            else:
                print(f"- Table {table_name} does not exist (skipping)")
        
        # Commit the changes
        conn.commit()
        print("\nDuplicate tables dropped successfully!")
        
        # Show remaining tables
        inspector = inspect(engine)
        remaining_tables = inspector.get_table_names()
        print(f"\nRemaining tables: {remaining_tables}")

if __name__ == "__main__":
    try:
        drop_duplicate_tables()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 