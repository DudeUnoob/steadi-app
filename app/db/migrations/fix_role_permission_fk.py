#!/usr/bin/env python
"""Migration script to fix the foreign key constraint in the role_permission table"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import logging
import sys

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

# SQL to drop the existing role_permission table and recreate it with correct FK
drop_and_recreate_sql = """
-- First drop the existing table
DROP TABLE IF EXISTS role_permission;

-- Recreate the table with the correct foreign key
CREATE TABLE role_permission (
    id UUID PRIMARY KEY,
    organization_id VARCHAR(10) NOT NULL,
    role VARCHAR(20) NOT NULL,
    permission_id VARCHAR(50) NOT NULL REFERENCES rules(id),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, role, permission_id)
);

-- Create index
CREATE INDEX idx_role_permission_org_id ON role_permission (organization_id);
"""

def run_migration():
    """Execute the migration script"""
    print("Starting database migration to fix role_permission foreign key...")
    logger.info("Starting database migration to fix role_permission foreign key...")
    
    transaction = None
    
    try:
        with engine.connect() as connection:
            # Start transaction
            transaction = connection.begin()
            
            # Drop and recreate the role_permission table
            print("Dropping and recreating role_permission table with correct foreign key...")
            logger.info("Dropping and recreating role_permission table with correct foreign key...")
            connection.execute(text(drop_and_recreate_sql))
            
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