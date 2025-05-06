from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from datetime import datetime
from uuid import UUID

from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.data_models.Supplier import Supplier
from app.models.enums.AlertLevel import AlertLevel

class MVPEditService:
    """Service for creating and modifying inventory data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Product management
    def create_product(self, product_data: Dict[str, Any], user_id: UUID) -> Product:
        """Create a new product"""
        try:
            # Add user_id to product data
            product_data["user_id"] = user_id
            
            # Check if product with same SKU already exists for this user
            existing = self.db.exec(select(Product).where(
                (Product.sku == product_data.get("sku")) &
                (Product.user_id == user_id)
            )).first()
            
            if existing:
                return {"error": "Product with this SKU already exists"}
            
            # Create new product
            product = Product(**product_data)
            
            # Set initial alert level
            self._update_product_alert_level(product)
            
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def update_product(self, product_id: UUID, product_data: Dict[str, Any], user_id: UUID) -> Product:
        """Update an existing product"""
        try:
            # Find product and verify ownership
            product = self.db.exec(select(Product).where(
                (Product.id == product_id) & 
                (Product.user_id == user_id)
            )).first()
            
            if not product:
                return {"error": "Product not found or you don't have permission to access it"}
            
            # Update fields
            for key, value in product_data.items():
                # Don't allow changing user_id
                if key != "user_id":
                    setattr(product, key, value)
            
            # Update alert level if inventory-related fields were changed
            inventory_fields = {"on_hand", "reorder_point", "safety_stock"}
            if any(field in product_data for field in inventory_fields):
                self._update_product_alert_level(product)
            
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def _update_product_alert_level(self, product: Product) -> None:
        """Update a product's alert level based on inventory levels"""
        # Handle None safety_stock by using 0 as default
        safety_stock = product.safety_stock if product.safety_stock is not None else 0
        
        if product.on_hand <= safety_stock:
            product.alert_level = AlertLevel.RED
        elif product.on_hand <= product.reorder_point:
            product.alert_level = AlertLevel.YELLOW
        else:
            product.alert_level = None
    
    def delete_product(self, product_id: UUID, user_id: UUID) -> Dict[str, str]:
        """Delete a product"""
        try:
            # Find product and verify ownership
            product = self.db.exec(select(Product).where(
                (Product.id == product_id) & 
                (Product.user_id == user_id)
            )).first()
            
            if not product:
                return {"error": "Product not found or you don't have permission to access it"}
            
            self.db.delete(product)
            self.db.commit()
            return {"message": "Product deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def get_products(self, user_id: UUID) -> List[Product]:
        """Get all products for a user"""
        try:
            products = self.db.exec(select(Product).where(
                Product.user_id == user_id
            )).all()
            return products
        except Exception as e:
            return {"error": str(e)}
    
    # Supplier management
    def create_supplier(self, supplier_data: Dict[str, Any], user_id: UUID) -> Supplier:
        """Create a new supplier"""
        try:
            # Add user_id to supplier data
            supplier_data["user_id"] = user_id
            
            # Check if supplier with same name already exists for this user
            existing = self.db.exec(select(Supplier).where(
                (Supplier.name == supplier_data.get("name")) &
                (Supplier.user_id == user_id)
            )).first()
            
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
    
    def update_supplier(self, supplier_id: UUID, supplier_data: Dict[str, Any], user_id: UUID) -> Supplier:
        """Update an existing supplier"""
        try:
            # Find supplier and verify ownership
            supplier = self.db.exec(select(Supplier).where(
                (Supplier.id == supplier_id) & 
                (Supplier.user_id == user_id)
            )).first()
            
            if not supplier:
                return {"error": "Supplier not found or you don't have permission to access it"}
            
            # Update fields
            for key, value in supplier_data.items():
                # Don't allow changing user_id
                if key != "user_id":
                    setattr(supplier, key, value)
            
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            return supplier
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def delete_supplier(self, supplier_id: UUID, user_id: UUID) -> Dict[str, str]:
        """Delete a supplier"""
        try:
            # Find supplier and verify ownership
            supplier = self.db.exec(select(Supplier).where(
                (Supplier.id == supplier_id) & 
                (Supplier.user_id == user_id)
            )).first()
            
            if not supplier:
                return {"error": "Supplier not found or you don't have permission to access it"}
            
            # Check if supplier has associated products
            products = self.db.exec(select(Product).where(
                (Product.supplier_id == supplier_id) &
                (Product.user_id == user_id)
            )).all()
            
            if products:
                return {"error": "Cannot delete supplier with associated products"}
            
            self.db.delete(supplier)
            self.db.commit()
            return {"message": "Supplier deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def get_suppliers(self, user_id: UUID) -> List[Supplier]:
        """Get all suppliers for a user"""
        try:
            suppliers = self.db.exec(select(Supplier).where(
                Supplier.user_id == user_id
            )).all()
            return suppliers
        except Exception as e:
            return {"error": str(e)}
    
    # Sale management
    def create_sale(self, sale_data: Dict[str, Any], user_id: UUID) -> Sale:
        """Create a new sale record"""
        try:
            # Add user_id to sale data
            sale_data["user_id"] = user_id
            
            # Ensure product exists and belongs to user
            product_id = sale_data.get("product_id")
            product = self.db.exec(select(Product).where(
                (Product.id == product_id) &
                (Product.user_id == user_id)
            )).first()
            
            if not product:
                return {"error": "Product not found or you don't have permission to access it"}
            
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
            
            # Update alert level
            self._update_product_alert_level(product)
            
            self.db.add(product)
            
            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def update_sale(self, sale_id: UUID, sale_data: Dict[str, Any], user_id: UUID) -> Sale:
        """Update an existing sale"""
        try:
            # Find sale and verify ownership
            sale = self.db.exec(select(Sale).where(
                (Sale.id == sale_id) & 
                (Sale.user_id == user_id)
            )).first()
            
            if not sale:
                return {"error": "Sale not found or you don't have permission to access it"}
            
            old_quantity = sale.quantity
            new_quantity = sale_data.get("quantity", old_quantity)
            
            # If quantity changed, update product inventory
            if "quantity" in sale_data and old_quantity != new_quantity:
                product = self.db.exec(select(Product).where(
                    (Product.id == sale.product_id) &
                    (Product.user_id == user_id)
                )).first()
                
                if not product:
                    return {"error": "Associated product not found or you don't have permission to access it"}
                
                # Restore original inventory
                product.on_hand += old_quantity
                
                # Apply new inventory change
                if product.on_hand < new_quantity:
                    return {"error": "Insufficient inventory"}
                product.on_hand -= new_quantity
                
                # Update alert level
                self._update_product_alert_level(product)
                
                self.db.add(product)
            
            # Update fields
            for key, value in sale_data.items():
                # Don't allow changing user_id
                if key != "user_id":
                    setattr(sale, key, value)
            
            self.db.add(sale)
            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def delete_sale(self, sale_id: UUID, user_id: UUID) -> Dict[str, str]:
        """Delete a sale and restore inventory"""
        try:
            # Find sale and verify ownership
            sale = self.db.exec(select(Sale).where(
                (Sale.id == sale_id) & 
                (Sale.user_id == user_id)
            )).first()
            
            if not sale:
                return {"error": "Sale not found or you don't have permission to access it"}
            
            # Restore inventory
            product = self.db.exec(select(Product).where(
                (Product.id == sale.product_id) &
                (Product.user_id == user_id)
            )).first()
            
            if product:
                product.on_hand += sale.quantity
                
                # Update alert level
                self._update_product_alert_level(product)
                
                self.db.add(product)
            
            # Delete sale
            self.db.delete(sale)
            self.db.commit()
            return {"message": "Sale deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def get_sales(self, user_id: UUID) -> List[Sale]:
        """Get all sales for a user"""
        try:
            sales = self.db.exec(select(Sale).where(
                Sale.user_id == user_id
            )).all()
            return sales
        except Exception as e:
            return {"error": str(e)} 