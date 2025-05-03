from sqlmodel import Session, select
from datetime import datetime, timedelta
import random
from uuid import uuid4

from app.db.database import engine
from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.data_models.Supplier import Supplier

def seed_data():
    # Create a database session
    with Session(engine) as db:
        # Create a supplier
        supplier = Supplier(
            id=uuid4(),
            name="Test Supplier",
            contact_email="supplier@test.com",
            lead_time_days=7
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        
        # Create some products
        products = []
        for i in range(10):
            product = Product(
                id=uuid4(),
                sku=f"TEST-{i:03d}",
                name=f"Test Product {i}",
                supplier_id=supplier.id,
                cost=random.uniform(10, 100),
                on_hand=random.randint(0, 100),
                reorder_point=random.randint(10, 30),
                safety_stock=random.randint(5, 15),
                lead_time_days=7
            )
            products.append(product)
            db.add(product)
        
        db.commit()
        
        # Create sales data for the last 30 days
        for product in products:
            for i in range(30):
                sale_date = datetime.utcnow() - timedelta(days=i)
                sale = Sale(
                    id=uuid4(),
                    product_id=product.id,
                    quantity=random.randint(0, 5),
                    sale_date=sale_date
                )
                db.add(sale)
        
        db.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_data() 