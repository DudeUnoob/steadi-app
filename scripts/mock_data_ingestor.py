import random
import string
from uuid import uuid4
from datetime import datetime

# Use Session from sqlmodel for type hinting if needed, but create SQLAlchemy session
from sqlmodel import SQLModel, Session as SQLModelSession, select
# Import SQLAlchemy session for actual use
from sqlalchemy.orm import Session as SQLAlchemySession

from app.models.data_models.Product import Product
from app.models.data_models.Supplier import Supplier
# Import engine directly
from app.db.database import engine, init_db

def generate_sku():
    """Generate a random SKU"""
    prefix = ''.join(random.choices(string.ascii_uppercase, k=4))
    number = random.randint(100, 999)
    return f"{prefix}-{number}"

# Use SQLAlchemySession for type hint here
def create_suppliers(session: SQLAlchemySession, count: int = 5):
    """Create mock suppliers"""
    suppliers = []
    for i in range(count):
        supplier = Supplier(
            id=uuid4(),
            name=f"Supplier {i+1}",
            contact_email=f"contact_supplier_{i+1}@example.com",
            phone=f"+1-555-01{i+1}-0000",
            lead_time_days=random.randint(3, 14)
        )
        session.add(supplier)
        suppliers.append(supplier)
    session.commit() # Commit within the function or after all creations in main
    # Refresh might be needed if IDs are used immediately after
    # for s in suppliers:
    #     session.refresh(s)
    return suppliers

# Use SQLAlchemySession for type hint here
def create_products(session: SQLAlchemySession, suppliers: list, count: int = 50):
    """Create mock products"""
    categories = ['Candle', 'Soap', 'Dress', 'Shirt', 'Book', 'Mug', 'Hat']
    for i in range(count):
        category = random.choice(categories)
        supplier = random.choice(suppliers)
        product = Product(
            id=uuid4(),
            sku=generate_sku(),
            name=f"{category} {i+1}",
            variant=random.choice(['Small', 'Medium', 'Large', None]),
            # Ensure supplier has an ID before accessing it
            supplier_id=supplier.id,
            cost=round(random.uniform(5.0, 50.0), 2),
            on_hand=random.randint(0, 100),
            reorder_point=random.randint(5, 20),
            safety_stock=random.randint(2, 10),
            lead_time_days=supplier.lead_time_days,
            created_at=datetime.utcnow()
        )
        session.add(product)
    session.commit() # Commit after adding all products

def main():
    """Initialize database with mock data"""
    init_db()  # Ensure tables are created

    # Create session directly using the engine for the script
    with SQLAlchemySession(engine) as session:
        # Check if data already exists
        # Use SQLAlchemy session execution syntax
        product_exists = session.execute(select(Product)).first()
        if product_exists:
            print("Products already exist in database. Skipping mock data creation.")
            return

        print("Creating mock suppliers...")
        suppliers = create_suppliers(session)
        # Ensure suppliers have their IDs populated if needed immediately
        # session.commit() # Commit here if create_suppliers doesn't
        # for s in suppliers: # Refresh if needed
        #     session.refresh(s)
        print(f"Created {len(suppliers)} suppliers.")

        print("Creating mock products...")
        create_products(session, suppliers)
        print(f"Created 50 products.")

        print("Mock data ingestion complete.")


if __name__ == "__main__":
    main()