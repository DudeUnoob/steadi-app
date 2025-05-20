"""
Migration script to add organization_id to all records based on the user's organization_id.
This script should be run after adding the organization_id field to all models.
"""

import logging
from sqlmodel import Session, select, text
from app.db.database import get_db
import uuid

logger = logging.getLogger(__name__)

def migrate_organization_id():
    """Add organization_id to all records based on user.organization_id"""
    db = next(get_db())
    
    try:
        # Get all users with organization_id using raw SQL to avoid importing User model
        # which can cause circular import issues with Rules
        result = db.execute(text('SELECT "id", "organization_id" FROM "user" WHERE "organization_id" IS NOT NULL'))
        users_with_org = [(str(row[0]), row[1]) for row in result.fetchall()]
        logger.info(f"Found {len(users_with_org)} users with organization_id")
        
        # Group users by organization_id
        users_by_org = {}
        for user_id, org_id in users_with_org:
            if org_id not in users_by_org:
                users_by_org[org_id] = []
            users_by_org[org_id].append(user_id)
            
        # For each organization, update all records
        for org_id, user_ids in users_by_org.items():
            logger.info(f"Updating records for organization {org_id} with {len(user_ids)} users")
            
            if not user_ids:  # Skip if no users
                continue
                
            # Ensure we have at least one user ID to avoid SQL errors with empty tuples
            if len(user_ids) == 1:
                user_ids = user_ids + user_ids  # Duplicate the single ID to make a valid tuple
            
            # Update products using raw SQL
            db.execute(
                text('UPDATE "product" SET "organization_id" = :org_id WHERE "user_id" IN :user_ids'),
                {"org_id": org_id, "user_ids": tuple(user_ids)}
            )
            db.commit()
            
            # Count updated products
            result = db.execute(
                text('SELECT COUNT(*) FROM "product" WHERE "organization_id" = :org_id'),
                {"org_id": org_id}
            )
            count = result.scalar()
            logger.info(f"Updated {count} products for organization {org_id}")
            
            # Update suppliers
            db.execute(
                text('UPDATE "supplier" SET "organization_id" = :org_id WHERE "user_id" IN :user_ids'),
                {"org_id": org_id, "user_ids": tuple(user_ids)}
            )
            db.commit()
            
            # Count updated suppliers
            result = db.execute(
                text('SELECT COUNT(*) FROM "supplier" WHERE "organization_id" = :org_id'),
                {"org_id": org_id}
            )
            count = result.scalar()
            logger.info(f"Updated {count} suppliers for organization {org_id}")
            
            # Update sales
            db.execute(
                text('UPDATE "sale" SET "organization_id" = :org_id WHERE "user_id" IN :user_ids'),
                {"org_id": org_id, "user_ids": tuple(user_ids)}
            )
            db.commit()
            
            # Count updated sales
            result = db.execute(
                text('SELECT COUNT(*) FROM "sale" WHERE "organization_id" = :org_id'),
                {"org_id": org_id}
            )
            count = result.scalar()
            logger.info(f"Updated {count} sales for organization {org_id}")
            
            # Update purchase orders
            db.execute(
                text('UPDATE "purchaseorder" SET "organization_id" = :org_id WHERE "created_by" IN :user_ids'),
                {"org_id": org_id, "user_ids": tuple(user_ids)}
            )
            db.commit()
            
            # Count updated purchase orders
            result = db.execute(
                text('SELECT COUNT(*) FROM "purchaseorder" WHERE "organization_id" = :org_id'),
                {"org_id": org_id}
            )
            count = result.scalar()
            logger.info(f"Updated {count} purchase orders for organization {org_id}")
            
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_organization_id() 