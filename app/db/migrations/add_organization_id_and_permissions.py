#!/usr/bin/env python
"""Migration script to add organization_id to user table and update rules table for permissions"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import logging
import sys
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable is not set!")
    print("Error: DATABASE_URL environment variable is not set!")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

# Current timestamp for created_at
current_time = datetime.utcnow().isoformat()

# SQL statements
add_organization_id_sql = """
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS organization_id VARCHAR(10);
CREATE INDEX IF NOT EXISTS idx_user_organization_id ON "user" (organization_id);
"""

# Ensure rules table has necessary columns
update_rules_table_sql = """
-- Add columns if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'rules' AND column_name = 'id') THEN
        ALTER TABLE rules ADD COLUMN id VARCHAR(50) PRIMARY KEY;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'rules' AND column_name = 'name') THEN
        ALTER TABLE rules ADD COLUMN name VARCHAR(100) NOT NULL DEFAULT '';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'rules' AND column_name = 'description') THEN
        ALTER TABLE rules ADD COLUMN description TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'rules' AND column_name = 'created_at') THEN
        ALTER TABLE rules ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'rules' AND column_name = 'updated_at') THEN
        ALTER TABLE rules ADD COLUMN updated_at TIMESTAMP;
    END IF;
END $$;
"""

create_role_permission_table_sql = """
CREATE TABLE IF NOT EXISTS role_permission (
    id UUID PRIMARY KEY,
    organization_id VARCHAR(10) NOT NULL,
    role VARCHAR(20) NOT NULL,
    permission_id VARCHAR(50) NOT NULL REFERENCES rules(id),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, role, permission_id)
);
CREATE INDEX IF NOT EXISTS idx_role_permission_org_id ON role_permission (organization_id);
"""

# Insert default permissions into rules table
insert_default_rules_sql = f"""
INSERT INTO rules (id, name, description, created_at) VALUES
('staff_view_products', 'View Products', 'Allow staff to view product information', '{current_time}'),
('staff_edit_products', 'Edit Products', 'Allow staff to edit product information', '{current_time}'),
('staff_view_suppliers', 'View Suppliers', 'Allow staff to view supplier information', '{current_time}'),
('staff_edit_suppliers', 'Edit Suppliers', 'Allow staff to edit supplier information', '{current_time}'),
('staff_view_sales', 'View Sales', 'Allow staff to view sales information', '{current_time}'),
('staff_edit_sales', 'Edit Sales', 'Allow staff to edit sales information', '{current_time}'),
('manager_view_products', 'View Products', 'Allow managers to view product information', '{current_time}'),
('manager_edit_products', 'Edit Products', 'Allow managers to edit product information', '{current_time}'),
('manager_view_suppliers', 'View Suppliers', 'Allow managers to view supplier information', '{current_time}'),
('manager_edit_suppliers', 'Edit Suppliers', 'Allow managers to edit supplier information', '{current_time}'),
('manager_view_sales', 'View Sales', 'Allow managers to view sales information', '{current_time}'),
('manager_edit_sales', 'Edit Sales', 'Allow managers to edit sales information', '{current_time}'),
('manager_set_staff_rules', 'Set Staff Rules', 'Allow managers to set permissions for staff members', '{current_time}')
ON CONFLICT (id) DO NOTHING;
"""

def run_migration():
    """Execute the migration script"""
    print("Starting database migration...")
    logger.info("Starting database migration...")
    
    transaction = None
    
    try:
        with engine.connect() as connection:
            # Start transaction
            transaction = connection.begin()
            
            # Add organization_id to user table
            print("Adding organization_id to user table...")
            logger.info("Adding organization_id to user table...")
            connection.execute(text(add_organization_id_sql))
            
            # Update rules table
            print("Ensuring rules table has necessary columns...")
            logger.info("Ensuring rules table has necessary columns...")
            connection.execute(text(update_rules_table_sql))
            
            # Create role_permission table
            print("Creating role_permission table...")
            logger.info("Creating role_permission table...")
            connection.execute(text(create_role_permission_table_sql))
            
            # Insert default permissions
            print("Inserting default rules...")
            logger.info("Inserting default rules...")
            connection.execute(text(insert_default_rules_sql))
            
            # Commit transaction
            transaction.commit()
            print("Migration completed successfully!")
            logger.info("Migration completed successfully")
            return True
            
    except Exception as e:
        # Rollback on error
        if transaction:
            transaction.rollback()
        error_msg = f"Error during migration: {str(e)}"
        print(f"Error: {error_msg}")
        logger.error(error_msg, exc_info=True)
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 