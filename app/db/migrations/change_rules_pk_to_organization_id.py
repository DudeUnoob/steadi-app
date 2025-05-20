import logging
import psycopg2
import os

logger = logging.getLogger(__name__)

def migrate():
    """
    Migration to change rules table primary key from user_id to organization_id.
    This is a destructive migration that will drop the existing rules table
    and recreate it with organization_id as the primary key.
    """
    logger.info("Starting migration: Change rules table primary key from user_id to organization_id")
    
    # Get database connection details from environment variables or use defaults
    DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
    DB_NAME = os.environ.get("POSTGRES_DB", "steadi")
    DB_USER = os.environ.get("POSTGRES_USER", "postgres")
    DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
    
    # SQL to drop existing rules table
    drop_table_sql = """
    DROP TABLE IF EXISTS rules CASCADE;
    """
    
    # SQL to create new rules table with organization_id as primary key
    create_table_sql = """
    CREATE TABLE rules (
        organization_id INTEGER PRIMARY KEY,
        staff_view_products BOOLEAN NOT NULL DEFAULT true,
        staff_edit_products BOOLEAN NOT NULL DEFAULT false,
        staff_view_suppliers BOOLEAN NOT NULL DEFAULT true,
        staff_edit_suppliers BOOLEAN NOT NULL DEFAULT false,
        staff_view_sales BOOLEAN NOT NULL DEFAULT true,
        staff_edit_sales BOOLEAN NOT NULL DEFAULT false,
        manager_view_products BOOLEAN NOT NULL DEFAULT true,
        manager_edit_products BOOLEAN NOT NULL DEFAULT true,
        manager_view_suppliers BOOLEAN NOT NULL DEFAULT true,
        manager_edit_suppliers BOOLEAN NOT NULL DEFAULT true,
        manager_view_sales BOOLEAN NOT NULL DEFAULT true,
        manager_edit_sales BOOLEAN NOT NULL DEFAULT true,
        manager_set_staff_rules BOOLEAN NOT NULL DEFAULT true
    );
    """
    
    # Connect to database and execute migrations
    try:
        logger.info(f"Connecting to PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        try:
            logger.info("Dropping existing rules table")
            cursor.execute(drop_table_sql)
            
            logger.info("Creating new rules table with organization_id as primary key")
            cursor.execute(create_table_sql)
            
            logger.info("Migration completed successfully")
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Set up logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    migrate() 