#!/usr/bin/env python3
"""
Script to check for duplicate suppliers in the database
Run this to see if there are existing suppliers that might be causing conflicts
"""

import sys
import os
from uuid import UUID

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlmodel import Session, select
from app.db.database import engine
from app.models.data_models.Supplier import Supplier
from app.models.data_models.User import User

def check_duplicate_suppliers():
    """Check for duplicate suppliers in the database"""
    try:
        with Session(engine) as session:
            # Get all suppliers with their user information
            suppliers = session.exec(
                select(Supplier, User)
                .join(User, Supplier.user_id == User.id)
                .order_by(Supplier.name, User.organization_id)
            ).all()
            
            if not suppliers:
                print("No suppliers found in the database.")
                return
            
            print("All suppliers in the database:")
            print("-" * 80)
            print(f"{'Name':<25} {'Email':<25} {'User ID':<15} {'Org ID':<10}")
            print("-" * 80)
            
            supplier_names = {}
            
            for supplier, user in suppliers:
                print(f"{supplier.name:<25} {supplier.contact_email or 'N/A':<25} {str(supplier.user_id)[:8]+'...':<15} {user.organization_id or 'N/A':<10}")
                
                # Track names by organization
                org_id = user.organization_id or 'NO_ORG'
                if org_id not in supplier_names:
                    supplier_names[org_id] = {}
                
                if supplier.name not in supplier_names[org_id]:
                    supplier_names[org_id][supplier.name] = []
                
                supplier_names[org_id][supplier.name].append({
                    'id': supplier.id,
                    'user_id': supplier.user_id,
                    'email': supplier.contact_email
                })
            
            print("\n" + "=" * 80)
            print("DUPLICATE CHECK BY ORGANIZATION:")
            print("=" * 80)
            
            duplicates_found = False
            for org_id, names in supplier_names.items():
                print(f"\nOrganization ID: {org_id}")
                print("-" * 40)
                
                for name, instances in names.items():
                    if len(instances) > 1:
                        duplicates_found = True
                        print(f"❌ DUPLICATE: '{name}' has {len(instances)} entries:")
                        for i, instance in enumerate(instances, 1):
                            print(f"   {i}. ID: {instance['id']}, User: {str(instance['user_id'])[:8]}..., Email: {instance['email'] or 'N/A'}")
                    else:
                        print(f"✅ '{name}' - OK")
            
            if not duplicates_found:
                print("\n✅ No duplicate supplier names found within organizations!")
            else:
                print(f"\n❌ Found duplicate suppliers! This might be causing the 'supplier already exists' error.")
                print("\nTo fix this, you can:")
                print("1. Rename one of the duplicate suppliers")
                print("2. Delete the duplicate supplier (if it has no associated products)")
                print("3. Check if the suppliers belong to different users in the same organization")
                
    except Exception as e:
        print(f"Error checking suppliers: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Checking for duplicate suppliers...")
    check_duplicate_suppliers() 