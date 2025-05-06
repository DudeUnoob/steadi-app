from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func
from datetime import datetime
from uuid import UUID
import logging

from app.models.data_models.Product import Product
from app.models.data_models.Sale import Sale
from app.models.data_models.Supplier import Supplier
from app.models.service_classes.InventoryService import InventoryService
from app.models.service_classes.AnalyticsService import AnalyticsService

logger = logging.getLogger(__name__)

class EditService:
    """Production service for creating and modifying inventory data with advanced features"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)
        self.analytics_service = AnalyticsService(db)
    
    # Product management
    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """Create a new product with validation and alerts setup"""
        try:
            # Check if product with same SKU already exists
            existing = self.db.exec(select(Product).where(Product.sku == product_data.get("sku"))).first()
            if existing:
                return {"error": "Product with this SKU already exists"}
            
            # Validate supplier exists
            supplier_id = product_data.get("supplier_id")
            if supplier_id:
                supplier = self.db.get(Supplier, supplier_id)
                if not supplier:
                    return {"error": "Supplier not found"}
                
                # Use supplier's lead time if not specified in product
                if not product_data.get("lead_time_days") and supplier.lead_time_days:
                    product_data["lead_time_days"] = supplier.lead_time_days
            
            # Create new product
            product = Product(**product_data)
            
            # Calculate initial alert level
            on_hand = product.on_hand
            reorder_point = product.reorder_point
            safety_stock = product.safety_stock or (reorder_point // 2)
            
            if on_hand <= safety_stock:
                product.alert_level = "RED"
            elif on_hand <= reorder_point:
                product.alert_level = "YELLOW"
            else:
                product.alert_level = "GREEN"
            
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            
            logger.info(f"Created product: {product.sku} - {product.name}")
            return product
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating product: {str(e)}")
            return {"error": str(e)}
    
    def update_product(self, product_id: UUID, product_data: Dict[str, Any]) -> Product:
        """Update an existing product with alert recalculation"""
        try:
            product = self.db.get(Product, product_id)
            if not product:
                return {"error": "Product not found"}
            
            # If supplier changed, validate new supplier exists
            if "supplier_id" in product_data:
                supplier_id = product_data["supplier_id"]
                supplier = self.db.get(Supplier, supplier_id)
                if not supplier:
                    return {"error": "Supplier not found"}
            
            # Update fields
            for key, value in product_data.items():
                setattr(product, key, value)
            
            # Recalculate alert level if inventory-related fields changed
            inventory_fields = {"on_hand", "reorder_point", "safety_stock"}
            if any(field in product_data for field in inventory_fields):
                on_hand = product.on_hand
                reorder_point = product.reorder_point
                safety_stock = product.safety_stock or (reorder_point // 2)
                
                if on_hand <= safety_stock:
                    product.alert_level = "RED"
                elif on_hand <= reorder_point:
                    product.alert_level = "YELLOW"
                else:
                    product.alert_level = "GREEN"
            
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            
            logger.info(f"Updated product: {product.sku} - {product.name}")
            return product
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating product: {str(e)}")
            return {"error": str(e)}
    
    def delete_product(self, product_id: UUID) -> Dict[str, str]:
        """Delete a product after checking dependencies"""
        try:
            product = self.db.get(Product, product_id)
            if not product:
                return {"error": "Product not found"}
            
            # Check if product has sales
            sales_count = self.db.exec(
                select(func.count()).select_from(Sale).where(Sale.product_id == product_id)
            ).one()
            
            if sales_count > 0:
                return {"error": f"Cannot delete product with {sales_count} associated sales"}
            
            sku = product.sku
            self.db.delete(product)
            self.db.commit()
            
            logger.info(f"Deleted product: {sku}")
            return {"message": f"Product {sku} deleted successfully"}
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting product: {str(e)}")
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
            
            logger.info(f"Created supplier: {supplier.name}")
            return supplier
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating supplier: {str(e)}")
            return {"error": str(e)}
    
    def update_supplier(self, supplier_id: UUID, supplier_data: Dict[str, Any]) -> Supplier:
        """Update an existing supplier with propagation to products"""
        try:
            supplier = self.db.get(Supplier, supplier_id)
            if not supplier:
                return {"error": "Supplier not found"}
            
            old_lead_time = supplier.lead_time_days
            
            # Update fields
            for key, value in supplier_data.items():
                setattr(supplier, key, value)
            
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            
            # If lead time changed, update products without custom lead times
            if "lead_time_days" in supplier_data and old_lead_time != supplier.lead_time_days:
                products = self.db.exec(select(Product).where(
                    (Product.supplier_id == supplier_id) & 
                    (Product.lead_time_days == old_lead_time)
                )).all()
                
                for product in products:
                    product.lead_time_days = supplier.lead_time_days
                    self.db.add(product)
                
                if products:
                    self.db.commit()
                    logger.info(f"Updated lead time for {len(products)} products from supplier {supplier.name}")
            
            logger.info(f"Updated supplier: {supplier.name}")
            return supplier
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating supplier: {str(e)}")
            return {"error": str(e)}
    
    def delete_supplier(self, supplier_id: UUID) -> Dict[str, str]:
        """Delete a supplier if no associated products"""
        try:
            supplier = self.db.get(Supplier, supplier_id)
            if not supplier:
                return {"error": "Supplier not found"}
            
            # Check if supplier has associated products
            products_count = self.db.exec(select(func.count()).select_from(Product).where(
                Product.supplier_id == supplier_id)).one()
                
            if products_count > 0:
                return {"error": f"Cannot delete supplier with {products_count} associated products"}
            
            name = supplier.name
            self.db.delete(supplier)
            self.db.commit()
            
            logger.info(f"Deleted supplier: {name}")
            return {"message": f"Supplier {name} deleted successfully"}
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting supplier: {str(e)}")
            return {"error": str(e)}
    
    # Sale management
    def create_sale(self, sale_data: Dict[str, Any]) -> Sale:
        """Create a new sale record with inventory updates and alerts"""
        try:
            # Ensure product exists
            product_id = sale_data.get("product_id")
            product = self.db.get(Product, product_id)
            if not product:
                return {"error": "Product not found"}
            
            # Check if we have enough inventory
            quantity = sale_data.get("quantity", 1)
            if product.on_hand < quantity:
                return {"error": f"Insufficient inventory: {product.on_hand} available, {quantity} requested"}
            
            # Create sale
            if "sale_date" not in sale_data:
                sale_data["sale_date"] = datetime.utcnow()
                
            sale = Sale(**sale_data)
            self.db.add(sale)
            
            # Update product inventory
            product.on_hand -= quantity
            
            # Update alert level if needed
            safety_stock = product.safety_stock or (product.reorder_point // 2)
            if product.on_hand <= safety_stock:
                product.alert_level = "RED"
            elif product.on_hand <= product.reorder_point:
                product.alert_level = "YELLOW"
            
            self.db.add(product)
            
            self.db.commit()
            self.db.refresh(sale)
            
            logger.info(f"Created sale: {quantity} units of {product.sku}")
            return sale
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating sale: {str(e)}")
            return {"error": str(e)}
    
    def update_sale(self, sale_id: UUID, sale_data: Dict[str, Any]) -> Sale:
        """Update an existing sale with inventory adjustments"""
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
                    return {"error": f"Insufficient inventory: {product.on_hand} available, {new_quantity} requested"}
                
                product.on_hand -= new_quantity
                
                # Update alert level
                safety_stock = product.safety_stock or (product.reorder_point // 2)
                if product.on_hand <= safety_stock:
                    product.alert_level = "RED"
                elif product.on_hand <= product.reorder_point:
                    product.alert_level = "YELLOW"
                else:
                    product.alert_level = "GREEN"
                    
                self.db.add(product)
            
            # Update sale fields
            for key, value in sale_data.items():
                setattr(sale, key, value)
            
            self.db.add(sale)
            self.db.commit()
            self.db.refresh(sale)
            
            logger.info(f"Updated sale: ID {sale_id}")
            return sale
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating sale: {str(e)}")
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
            
            # Update alert level
            safety_stock = product.safety_stock or (product.reorder_point // 2)
            if product.on_hand > product.reorder_point:
                product.alert_level = "GREEN"
            elif product.on_hand > safety_stock:
                product.alert_level = "YELLOW"
                
            self.db.add(product)
            
            # Delete sale
            self.db.delete(sale)
            self.db.commit()
            
            logger.info(f"Deleted sale: ID {sale_id}")
            return {"message": "Sale deleted successfully"}
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting sale: {str(e)}")
            return {"error": str(e)} 