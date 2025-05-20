"""
Script to add organization_id columns to database tables.
This should be run before attempting the data migration.
"""

import logging
from sqlmodel import Session, text
from app.db.database import get_db

logger = logging.getLogger(__name__)

def add_organization_id_columns():
    """Add organization_id column to tables that need it"""
    db = next(get_db())
    
    try:
        # Tables that need the organization_id column
        tables = ['product', 'supplier', 'sale', 'purchaseorder']
        
        for table in tables:
            try:
                # Add organization_id column if it doesn't exist
                db.execute(text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "organization_id" INTEGER;'))
                db.commit()
                logger.info(f"Added organization_id column to {table} table")
            except Exception as e:
                logger.error(f"Error adding organization_id to {table}: {str(e)}")
                db.rollback()
        
        logger.info("Column additions completed")
        
    except Exception as e:
        logger.error(f"Error during column additions: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    add_organization_id_columns() 