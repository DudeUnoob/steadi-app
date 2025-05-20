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
    
   
    def create_product(self, product_data: Dict[str, Any], user_id: UUID, organization_id: int = None) -> Product:
        """Create a new product"""
        try:
            # Ensure user_id and organization_id are set
            product_data["user_id"] = user_id
            if organization_id:
                product_data["organization_id"] = organization_id
            
            # Check if product with same SKU already exists in this organization
            query = select(Product).where(Product.sku == product_data.get("sku"))
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Product.organization_id == organization_id)
            else:
                query = query.where(Product.user_id == user_id)
                
            existing = self.db.exec(query).first()
            
            if existing:
                return {"error": "Product with this SKU already exists"}
            
            # Create new product
            product = Product(**product_data)
            
            # Update alert level
            self._update_product_alert_level(product)
            
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def update_product(self, product_id: UUID, product_data: Dict[str, Any], user_id: UUID, organization_id: int = None) -> Product:
        """Update an existing product"""
        try:
            # Find product by ID and ensure it belongs to the organization/user
            query = select(Product).where(Product.id == product_id)
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Product.organization_id == organization_id)
            else:
                query = query.where(Product.user_id == user_id)
                
            product = self.db.exec(query).first()
            
            if not product:
                return {"error": "Product not found or you don't have permission to access it"}
            
            # Update fields but don't allow changing user_id or organization_id
            for key, value in product_data.items():
                if key not in ["user_id", "organization_id"]:
                    setattr(product, key, value)
            
            # Update alert level if inventory-related fields changed
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
       
        safety_stock = product.safety_stock if product.safety_stock is not None else 0
        
        if product.on_hand <= safety_stock:
            product.alert_level = AlertLevel.RED
        elif product.on_hand <= product.reorder_point:
            product.alert_level = AlertLevel.YELLOW
        else:
            product.alert_level = None
    
    def delete_product(self, product_id: UUID, user_id: UUID, organization_id: int = None) -> Dict[str, str]:
        """Delete a product"""
        try:
            # Find product by ID and ensure it belongs to the organization/user
            query = select(Product).where(Product.id == product_id)
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Product.organization_id == organization_id)
            else:
                query = query.where(Product.user_id == user_id)
                
            product = self.db.exec(query).first()
            
            if not product:
                return {"error": "Product not found or you don't have permission to access it"}
            
            self.db.delete(product)
            self.db.commit()
            return {"message": "Product deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def get_products(self, user_id: UUID, organization_id: int = None) -> List[Product]:
        """Get all products for a user or organization"""
        try:
            query = select(Product)
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Product.organization_id == organization_id)
            else:
                query = query.where(Product.user_id == user_id)
                
            products = self.db.exec(query).all()
            return products
        except Exception as e:
            return {"error": str(e)}
    
    # Supplier management
    def create_supplier(self, supplier_data: Dict[str, Any], user_id: UUID, organization_id: int = None) -> Supplier:
        """Create a new supplier"""
        try:
            # Ensure user_id and organization_id are set
            supplier_data["user_id"] = user_id
            if organization_id:
                supplier_data["organization_id"] = organization_id
            
            # Check if supplier with same name already exists in this organization
            query = select(Supplier).where(Supplier.name == supplier_data.get("name"))
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Supplier.organization_id == organization_id)
            else:
                query = query.where(Supplier.user_id == user_id)
                
            existing = self.db.exec(query).first()
            
            if existing:
                return {"error": "Supplier with this name already exists"}
            
            # Handle lead_time_days specifically - use default if None
            if "lead_time_days" in supplier_data and supplier_data["lead_time_days"] is None:
                supplier_data["lead_time_days"] = 7  # Default value from the model
            
            supplier = Supplier(**supplier_data)
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            return supplier
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def update_supplier(self, supplier_id: UUID, supplier_data: Dict[str, Any], user_id: UUID, organization_id: int = None) -> Supplier:
        """Update an existing supplier"""
        try:
            # Find supplier by ID and ensure it belongs to the organization/user
            query = select(Supplier).where(Supplier.id == supplier_id)
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Supplier.organization_id == organization_id)
            else:
                query = query.where(Supplier.user_id == user_id)
                
            supplier = self.db.exec(query).first()
            
            if not supplier:
                return {"error": "Supplier not found or you don't have permission to access it"}
            
            # If changing the name, check for duplicates
            if "name" in supplier_data and supplier_data["name"] != supplier.name:
                name_query = select(Supplier).where(Supplier.name == supplier_data["name"])
                
                # Apply same org/user filter
                if organization_id:
                    name_query = name_query.where(Supplier.organization_id == organization_id)
                else:
                    name_query = name_query.where(Supplier.user_id == user_id)
                    
                existing = self.db.exec(name_query).first()
                if existing:
                    return {"error": "Supplier with this name already exists"}
            
            # Update fields but don't allow changing user_id or organization_id
            for key, value in supplier_data.items():
                if key not in ["user_id", "organization_id"]:
                    setattr(supplier, key, value)
            
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            return supplier
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def delete_supplier(self, supplier_id: UUID, user_id: UUID, organization_id: int = None) -> Dict[str, str]:
        """Delete a supplier"""
        try:
            # Find supplier by ID and ensure it belongs to the organization/user
            query = select(Supplier).where(Supplier.id == supplier_id)
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Supplier.organization_id == organization_id)
            else:
                query = query.where(Supplier.user_id == user_id)
                
            supplier = self.db.exec(query).first()
            
            if not supplier:
                return {"error": "Supplier not found or you don't have permission to access it"}
            
            # Check for associated products
            product_query = select(Product).where(Product.supplier_id == supplier_id)
            
            # Apply the same organization/user filter to products
            if organization_id:
                product_query = product_query.where(Product.organization_id == organization_id)
            else:
                product_query = product_query.where(Product.user_id == user_id)
                
            products = self.db.exec(product_query).all()
            
            if products:
                return {"error": "Cannot delete supplier with associated products"}
            
            self.db.delete(supplier)
            self.db.commit()
            return {"message": "Supplier deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def get_suppliers(self, user_id: UUID, organization_id: int = None) -> List[Dict[str, Any]]:
        """Get all suppliers for a user or organization with product count"""
        try:
            # First get all suppliers
            query = select(Supplier)
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Supplier.organization_id == organization_id)
            else:
                query = query.where(Supplier.user_id == user_id)
                
            suppliers = self.db.exec(query).all()
            
            # Convert to list of dictionaries for easier manipulation
            result = []
            for supplier in suppliers:
                # For each supplier, count the number of associated products
                product_query = select(Product).where(Product.supplier_id == supplier.id)
                
                # Apply the same organization/user filter to products
                if organization_id:
                    product_query = product_query.where(Product.organization_id == organization_id)
                else:
                    product_query = product_query.where(Product.user_id == user_id)
                    
                products = self.db.exec(product_query).all()
                
                product_count = len(products)
                
                # Convert supplier to dict and add product count
                supplier_dict = {
                    "id": supplier.id,
                    "name": supplier.name,
                    "contact_email": supplier.contact_email,
                    "phone": supplier.phone,
                    "lead_time_days": supplier.lead_time_days,
                    "notes": supplier.notes,
                    "created_at": supplier.created_at,
                    "user_id": supplier.user_id,
                    "organization_id": supplier.organization_id,
                    "product_count": product_count
                }
                
                result.append(supplier_dict)
                
            return result
        except Exception as e:
            return {"error": str(e)}
    
    
    def create_sale(self, sale_data: Dict[str, Any], user_id: UUID, organization_id: int = None) -> Sale:
        """Create a new sale record"""
        try:
            # Ensure user_id and organization_id are set
            sale_data["user_id"] = user_id
            if organization_id:
                sale_data["organization_id"] = organization_id
            
            # Ensure product exists and belongs to the organization/user
            product_id = sale_data.get("product_id")
            product_query = select(Product).where(Product.id == product_id)
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                product_query = product_query.where(Product.organization_id == organization_id)
            else:
                product_query = product_query.where(Product.user_id == user_id)
                
            product = self.db.exec(product_query).first()
            
            if not product:
                return {"error": "Product not found or you don't have permission to access it"}
            
            # Check inventory
            quantity = sale_data.get("quantity", 1)
            if product.on_hand < quantity:
                return {"error": "Insufficient inventory"}
            
            # Set sale date if not provided
            if "sale_date" not in sale_data:
                sale_data["sale_date"] = datetime.utcnow()
                
            sale = Sale(**sale_data)
            self.db.add(sale)
            
            # Update inventory
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
    
    def update_sale(self, sale_id: UUID, sale_data: Dict[str, Any], user_id: UUID, organization_id: int = None) -> Sale:
        """Update an existing sale"""
        try:
            # Find sale by ID and ensure it belongs to the organization/user
            query = select(Sale).where(Sale.id == sale_id)
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Sale.organization_id == organization_id)
            else:
                query = query.where(Sale.user_id == user_id)
                
            sale = self.db.exec(query).first()
            
            if not sale:
                return {"error": "Sale not found or you don't have permission to access it"}
            
            old_quantity = sale.quantity
            new_quantity = sale_data.get("quantity", old_quantity)
            
            # Update inventory if quantity changed
            if "quantity" in sale_data and old_quantity != new_quantity:
                # Find the product using the same org/user filter
                product_query = select(Product).where(Product.id == sale.product_id)
                
                if organization_id:
                    product_query = product_query.where(Product.organization_id == organization_id)
                else:
                    product_query = product_query.where(Product.user_id == user_id)
                    
                product = self.db.exec(product_query).first()
                
                if not product:
                    return {"error": "Associated product not found or you don't have permission to access it"}
                
                # Restore original inventory
                product.on_hand += old_quantity
                
                # Check for sufficient inventory
                if product.on_hand < new_quantity:
                    return {"error": "Insufficient inventory"}
                product.on_hand -= new_quantity
                
                # Update alert level
                self._update_product_alert_level(product)
                
                self.db.add(product)
            
            # Update fields but don't allow changing user_id or organization_id
            for key, value in sale_data.items():
                if key not in ["user_id", "organization_id"]:
                    setattr(sale, key, value)
            
            self.db.add(sale)
            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}
    
    def delete_sale(self, sale_id: UUID, user_id: UUID, organization_id: int = None) -> Dict[str, str]:
        """Delete a sale and restore inventory"""
        try:
            # Find sale by ID and ensure it belongs to the organization/user
            query = select(Sale).where(Sale.id == sale_id)
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Sale.organization_id == organization_id)
            else:
                query = query.where(Sale.user_id == user_id)
                
            sale = self.db.exec(query).first()
            
            if not sale:
                return {"error": "Sale not found or you don't have permission to access it"}
            
            # Find the product using the same org/user filter
            product_query = select(Product).where(Product.id == sale.product_id)
            
            if organization_id:
                product_query = product_query.where(Product.organization_id == organization_id)
            else:
                product_query = product_query.where(Product.user_id == user_id)
                
            product = self.db.exec(product_query).first()
            
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
    
    def get_sales(self, user_id: UUID, organization_id: int = None) -> List[Sale]:
        """Get all sales for a user or organization"""
        try:
            query = select(Sale)
            
            # Filter by organization if available, otherwise fallback to user_id
            if organization_id:
                query = query.where(Sale.organization_id == organization_id)
            else:
                query = query.where(Sale.user_id == user_id)
                
            sales = self.db.exec(query).all()
            return sales
        except Exception as e:
            return {"error": str(e)} 