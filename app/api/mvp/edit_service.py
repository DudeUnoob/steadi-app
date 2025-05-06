from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from datetime import datetime
from uuid import UUID

from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.data_models.Supplier import Supplier

class MVPEditService:
    """Service for creating and modifying inventory data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Product management
    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """Create a new product"""
        try:
            # Check if product with same SKU already exists
            existing = self.db.exec(select(Product).where(Product.sku == product_data.get("sku"))).first()
            if existing:
                return {"error": "Product with this SKU already exists"}
            
            # Create new product
            product = Product(**product_data)
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def update_product(self, product_id: UUID, product_data: Dict[str, Any]) -> Product:
        """Update an existing product"""
        try:
            product = self.db.get(Product, product_id)
            if not product:
                return {"error": "Product not found"}
            
            # Update fields
            for key, value in product_data.items():
                setattr(product, key, value)
            
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def delete_product(self, product_id: UUID) -> Dict[str, str]:
        """Delete a product"""
        try:
            product = self.db.get(Product, product_id)
            if not product:
                return {"error": "Product not found"}
            
            self.db.delete(product)
            self.db.commit()
            return {"message": "Product deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    # Supplier management
    def create_supplier(self, supplier_data: Dict[str, Any]) -> Supplier:
        """Create a new supplier"""
        try:
            # Check if supplier with same name already exists
            existing = self.db.exec(select(Supplier).where(
                Supplier.name == supplier_data.get("name"))).first()
            if existing:
                return {"error": "Supplier with this name already exists"}
            
            # Create new supplier
            supplier = Supplier(**supplier_data)
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            return supplier
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def update_supplier(self, supplier_id: UUID, supplier_data: Dict[str, Any]) -> Supplier:
        """Update an existing supplier"""
        try:
            supplier = self.db.get(Supplier, supplier_id)
            if not supplier:
                return {"error": "Supplier not found"}
            
            # Update fields
            for key, value in supplier_data.items():
                setattr(supplier, key, value)
            
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            return supplier
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def delete_supplier(self, supplier_id: UUID) -> Dict[str, str]:
        """Delete a supplier"""
        try:
            supplier = self.db.get(Supplier, supplier_id)
            if not supplier:
                return {"error": "Supplier not found"}
            
            # Check if supplier has associated products
            products = self.db.exec(select(Product).where(
                Product.supplier_id == supplier_id)).all()
            if products:
                return {"error": "Cannot delete supplier with associated products"}
            
            self.db.delete(supplier)
            self.db.commit()
            return {"message": "Supplier deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    # Sale management
    def create_sale(self, sale_data: Dict[str, Any]) -> Sale:
        """Create a new sale record"""
        try:
            # Ensure product exists
            product_id = sale_data.get("product_id")
            product = self.db.get(Product, product_id)
            if not product:
                return {"error": "Product not found"}
            
            # Check if we have enough inventory
            quantity = sale_data.get("quantity", 1)
            if product.on_hand < quantity:
                return {"error": "Insufficient inventory"}
            
            # Create sale
            if "sale_date" not in sale_data:
                sale_data["sale_date"] = datetime.utcnow()
                
            sale = Sale(**sale_data)
            self.db.add(sale)
            
            # Update product inventory
            product.on_hand -= quantity
            self.db.add(product)
            
            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def update_sale(self, sale_id: UUID, sale_data: Dict[str, Any]) -> Sale:
        """Update an existing sale"""
        try:
            sale = self.db.get(Sale, sale_id)
            if not sale:
                return {"error": "Sale not found"}
            
            old_quantity = sale.quantity
            new_quantity = sale_data.get("quantity", old_quantity)
            
            # If quantity changed, update product inventory
            if "quantity" in sale_data and old_quantity != new_quantity:
                product = self.db.get(Product, sale.product_id)
                
                # Restore original inventory
                product.on_hand += old_quantity
                
                # Apply new inventory change
                if product.on_hand < new_quantity:
                    return {"error": "Insufficient inventory"}
                product.on_hand -= new_quantity
                self.db.add(product)
            
            # Update fields
            for key, value in sale_data.items():
                setattr(sale, key, value)
            
            self.db.add(sale)
            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def delete_sale(self, sale_id: UUID) -> Dict[str, str]:
        """Delete a sale and restore inventory"""
        try:
            sale = self.db.get(Sale, sale_id)
            if not sale:
                return {"error": "Sale not found"}
            
            # Restore inventory
            product = self.db.get(Product, sale.product_id)
            product.on_hand += sale.quantity
            self.db.add(product)
            
            # Delete sale
            self.db.delete(sale)
            self.db.commit()
            return {"message": "Sale deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)} 