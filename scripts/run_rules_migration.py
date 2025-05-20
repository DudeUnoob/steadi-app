#!/usr/bin/env python3
"""
Script to run the migration that changes the rules table
primary key from user_id to organization_id.
"""
import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Remove dotenv dependency
# from dotenv import load_dotenv
# load_dotenv()

# Import the migration
from app.db.migrations.change_rules_pk_to_organization_id import migrate

if __name__ == "__main__":
    print("Starting migration to change rules table primary key to organization_id...")
    try:
        migrate()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        sys.exit(1) 