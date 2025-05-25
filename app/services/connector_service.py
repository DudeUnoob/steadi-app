import csv
import io
import aiohttp
import logging
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from uuid import UUID
from sqlmodel import Session, select
from fastapi import HTTPException, UploadFile

from app.models.data_models.Connector import Connector
from app.models.data_models.Product import Product
from app.models.data_models.Supplier import Supplier
from app.models.data_models.InventoryLedger import InventoryLedger
from app.models.data_models.Alert import Alert
from app.models.data_models.AuditLog import AuditLog
from app.models.enums.ConnectorProvider import ConnectorProvider
from app.models.enums.AlertType import AlertType
from app.models.enums.AuditAction import AuditAction
from app.schemas.data_models.Connector import (
    ConnectorSync, 
    CSVUploadResponse, 
    ConnectorTestResponse
)

logger = logging.getLogger(__name__)

class ConnectorService:
    """Manages external system connections and synchronization"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def sync_shopify(self, connector_id: UUID) -> ConnectorSync:
        """Sync inventory from Shopify using Admin API"""
        connector = self.db.exec(select(Connector).where(Connector.id == connector_id)).first()
        if not connector:
            raise HTTPException(status_code=404, detail="Connector not found")
        
        if connector.provider != ConnectorProvider.SHOPIFY:
            raise HTTPException(status_code=400, detail="Invalid provider for Shopify sync")
        
        sync_started_at = datetime.utcnow()
        items_synced = 0
        items_updated = 0
        items_created = 0
        errors = []
        
        try:
            shop_domain = connector.config.get("shop_domain") if connector.config else None
            if not shop_domain:
                raise ValueError("Shop domain not configured")
            
            headers = {
                "X-Shopify-Access-Token": connector.access_token,
                "Content-Type": "application/json"
            }
            
            # Use the latest API version (2025-01)
            base_url = f"https://{shop_domain}/admin/api/2025-01"
            
            async with aiohttp.ClientSession() as session:
                # First, get all locations
                locations_url = f"{base_url}/locations.json"
                async with session.get(locations_url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Shopify Locations API error: {error_text}"
                        )
                    
                    locations_data = await response.json()
                    locations = locations_data.get("locations", [])
                    
                    if not locations:
                        raise ValueError("No locations found in Shopify store")
                    
                    # Use the first location (typically the main location)
                    primary_location_id = locations[0]["id"]
                
                # Get all products with their variants
                products_url = f"{base_url}/products.json?limit=250"
                page_info = None
                total_products_processed = 0
                
                while True:
                    url = products_url
                    if page_info:
                        url = f"{base_url}/products.json?limit=250&page_info={page_info}"
                    
                    logger.info(f"Fetching products from: {url}")
                    
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise HTTPException(
                                status_code=response.status,
                                detail=f"Shopify Products API error: {error_text}"
                            )
                        
                        products_data = await response.json()
                        products = products_data.get("products", [])
                        
                        logger.info(f"Processing {len(products)} products from this page")
                        total_products_processed += len(products)
                        
                        # Process each product and its variants
                        for product in products:
                            product_title = product.get("title", "")
                            variants = product.get("variants", [])
                            
                            logger.debug(f"Processing product: {product_title} with {len(variants)} variants")
                            
                            for variant in variants:
                                variant_id = variant.get("id")
                                sku = variant.get("sku")
                                
                                if not sku:
                                    # Skip variants without SKU
                                    logger.info(f"Skipping variant {variant_id} of '{product_title}' - no SKU")
                                    continue
                                
                                variant_title = variant.get("title", "")
                                price = float(variant.get("price", 0))
                                
                                logger.debug(f"Processing variant: {variant_title} (SKU: {sku})")
                                
                                # Get inventory level for this variant at the primary location
                                inventory_item_id = variant.get("inventory_item_id")
                                if not inventory_item_id:
                                    logger.warning(f"No inventory_item_id for variant {variant_id} (SKU: {sku})")
                                    continue
                                
                                inventory_url = f"{base_url}/inventory_levels.json?inventory_item_ids={inventory_item_id}&location_ids={primary_location_id}"
                                
                                async with session.get(inventory_url, headers=headers) as inv_response:
                                    if inv_response.status == 200:
                                        inv_data = await inv_response.json()
                                        inventory_levels = inv_data.get("inventory_levels", [])
                                        
                                        available_quantity = 0
                                        if inventory_levels:
                                            available_quantity = inventory_levels[0].get("available", 0)
                                        
                                        # Build product name with variant info
                                        full_name = product_title
                                        if variant_title and variant_title != "Default Title":
                                            full_name = f"{product_title} - {variant_title}"
                                        
                                        logger.info(f"Syncing product: {sku} - {full_name} (Qty: {available_quantity})")
                                        
                                        # Update or create product
                                        result = await self._update_or_create_product(
                                            sku=sku,
                                            name=full_name,
                                            variant=variant_title if variant_title != "Default Title" else None,
                                            on_hand=available_quantity,
                                            cost=price,  # Use price as cost estimate
                                            source="shopify",
                                            reference_id=str(variant_id),
                                            user_id=connector.created_by
                                        )
                                        
                                        items_synced += 1
                                        if result["created"]:
                                            items_created += 1
                                            logger.info(f"Created new product: {sku}")
                                        else:
                                            items_updated += 1
                                            logger.info(f"Updated existing product: {sku}")
                                            
                                        logger.debug(f"Processed product: {sku} - {full_name}")
                                    else:
                                        error_text = await inv_response.text()
                                        logger.warning(f"Failed to get inventory for variant {variant_id} (SKU: {sku}): {error_text}")
                        
                        # Check for pagination using Link header
                        link_header = response.headers.get("Link")
                        page_info = None
                        
                        if link_header and "rel=\"next\"" in link_header:
                            # Extract page_info from Link header
                            # Format: <https://shop.myshopify.com/admin/api/2025-01/products.json?limit=250&page_info=xyz>; rel="next"
                            import re
                            next_match = re.search(r'<[^>]*[?&]page_info=([^&>]+)[^>]*>;\s*rel="next"', link_header)
                            if next_match:
                                page_info = next_match.group(1)
                                logger.info(f"Found next page with page_info: {page_info}")
                            else:
                                logger.info("No valid page_info found in Link header, ending pagination")
                                break
                        else:
                            logger.info("No next page found, ending pagination")
                            break
                
                logger.info(f"Shopify sync completed. Total products processed: {total_products_processed}, Items synced: {items_synced}")
            
            # Update connector last sync time
            connector.last_sync = datetime.utcnow()
            connector.status = "ACTIVE"
            self.db.add(connector)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Shopify sync error: {str(e)}")
            errors.append(str(e))
            connector.status = "ERROR"
            self.db.add(connector)
            self.db.commit()
        
        return ConnectorSync(
            connector_id=connector_id,
            provider=ConnectorProvider.SHOPIFY,
            status=connector.status,
            items_synced=items_synced,
            items_updated=items_updated,
            items_created=items_created,
            sync_started_at=sync_started_at,
            sync_completed_at=datetime.utcnow(),
            errors=errors
        )
    
    async def sync_square(self, connector_id: UUID) -> ConnectorSync:
        """Sync inventory from Square Inventory API"""
        connector = self.db.exec(select(Connector).where(Connector.id == connector_id)).first()
        if not connector:
            raise HTTPException(status_code=404, detail="Connector not found")
        
        if connector.provider != ConnectorProvider.SQUARE:
            raise HTTPException(status_code=400, detail="Invalid provider for Square sync")
        
        sync_started_at = datetime.utcnow()
        items_synced = 0
        items_updated = 0
        items_created = 0
        errors = []
        
        try:
            headers = {
                "Authorization": f"Bearer {connector.access_token}",
                "Content-Type": "application/json",
                "Square-Version": "2025-04-16"
            }
            
            # Get inventory changes
            url = "https://connect.squareup.com/v2/inventory/changes/batch-retrieve"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={}) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Square API error: {error_text}"
                        )
                    
                    data = await response.json()
                    changes = data.get("changes", [])
                    
                    for change in changes:
                        if change.get("type") != "PHYSICAL_COUNT":
                            continue
                        
                        physical_count = change.get("physical_count", {})
                        catalog_object_id = physical_count.get("catalog_object_id")
                        quantity = int(physical_count.get("quantity", 0))
                        
                        if not catalog_object_id:
                            continue
                        
                        # Get catalog item details
                        catalog_url = f"https://connect.squareup.com/v2/catalog/object/{catalog_object_id}"
                        async with session.get(catalog_url, headers=headers) as catalog_response:
                            if catalog_response.status == 200:
                                catalog_data = await catalog_response.json()
                                catalog_object = catalog_data.get("object", {})
                                item_variation_data = catalog_object.get("item_variation_data", {})
                                
                                sku = item_variation_data.get("sku", catalog_object_id)
                                name = item_variation_data.get("name", "Unknown Product")
                                
                                # Get price if available
                                cost = 0.0
                                price_money = item_variation_data.get("price_money")
                                if price_money:
                                    cost = float(price_money.get("amount", 0)) / 100  # Square uses cents
                                
                                result = await self._update_or_create_product(
                                    sku=sku,
                                    name=name,
                                    on_hand=quantity,
                                    cost=cost,
                                    source="square",
                                    reference_id=catalog_object_id,
                                    user_id=connector.created_by
                                )
                                
                                items_synced += 1
                                if result["created"]:
                                    items_created += 1
                                else:
                                    items_updated += 1
            
            # Update connector
            connector.last_sync = datetime.utcnow()
            connector.status = "ACTIVE"
            self.db.add(connector)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Square sync error: {str(e)}")
            errors.append(str(e))
            connector.status = "ERROR"
            self.db.add(connector)
            self.db.commit()
        
        return ConnectorSync(
            connector_id=connector_id,
            provider=ConnectorProvider.SQUARE,
            status=connector.status,
            items_synced=items_synced,
            items_updated=items_updated,
            items_created=items_created,
            sync_started_at=sync_started_at,
            sync_completed_at=datetime.utcnow(),
            errors=errors
        )
    
    async def sync_lightspeed(self, connector_id: UUID) -> ConnectorSync:
        """Sync inventory from Lightspeed Retail API"""
        connector = self.db.exec(select(Connector).where(Connector.id == connector_id)).first()
        if not connector:
            raise HTTPException(status_code=404, detail="Connector not found")
        
        if connector.provider != ConnectorProvider.LIGHTSPEED:
            raise HTTPException(status_code=400, detail="Invalid provider for Lightspeed sync")
        
        sync_started_at = datetime.utcnow()
        items_synced = 0
        items_updated = 0
        items_created = 0
        errors = []
        
        try:
            account_id = connector.config.get("account_id") if connector.config else None
            if not account_id:
                raise ValueError("Account ID not configured")
            
            headers = {
                "Authorization": f"Bearer {connector.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get items from Lightspeed
            url = f"https://api.lightspeedapp.com/API/Account/{account_id}/Item.json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Lightspeed API error: {error_text}"
                        )
                    
                    data = await response.json()
                    items = data.get("Item", [])
                    
                    # Ensure items is a list
                    if not isinstance(items, list):
                        items = [items] if items else []
                    
                    for item in items:
                        sku = item.get("customSku") or item.get("systemSku", "")
                        if not sku:
                            continue
                        
                        name = item.get("description", "Unknown Product")
                        quantity = int(item.get("qtyOnHand", 0))
                        cost = float(item.get("defaultCost", 0))
                        
                        result = await self._update_or_create_product(
                            sku=sku,
                            name=name,
                            on_hand=quantity,
                            cost=cost,
                            source="lightspeed",
                            reference_id=str(item.get("itemID", "")),
                            user_id=connector.created_by
                        )
                        
                        items_synced += 1
                        if result["created"]:
                            items_created += 1
                        else:
                            items_updated += 1
            
            # Update connector
            connector.last_sync = datetime.utcnow()
            connector.status = "ACTIVE"
            self.db.add(connector)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Lightspeed sync error: {str(e)}")
            errors.append(str(e))
            connector.status = "ERROR"
            self.db.add(connector)
            self.db.commit()
        
        return ConnectorSync(
            connector_id=connector_id,
            provider=ConnectorProvider.LIGHTSPEED,
            status=connector.status,
            items_synced=items_synced,
            items_updated=items_updated,
            items_created=items_created,
            sync_started_at=sync_started_at,
            sync_completed_at=datetime.utcnow(),
            errors=errors
        )
    
    async def import_csv(
        self, 
        file: UploadFile, 
        sku_column: str,
        name_column: str,
        on_hand_column: str,
        cost_column: Optional[str] = None,
        supplier_name_column: Optional[str] = None,
        variant_column: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> CSVUploadResponse:
        """Enhanced CSV import with comprehensive workflow"""
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Initialize counters and tracking
        imported_items = 0
        updated_items = 0
        created_items = 0
        errors = []
        warnings = []
        duplicate_skus = set()
        processed_skus = set()
        validation_errors = []
        threshold_updates = []
        
        try:
            # Step 1: Read and parse CSV content
            content = await file.read()
            csv_content = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Validate required columns
            if sku_column not in csv_reader.fieldnames:
                raise HTTPException(status_code=400, detail=f"SKU column '{sku_column}' not found")
            if name_column not in csv_reader.fieldnames:
                raise HTTPException(status_code=400, detail=f"Name column '{name_column}' not found")
            if on_hand_column not in csv_reader.fieldnames:
                raise HTTPException(status_code=400, detail=f"Quantity column '{on_hand_column}' not found")
            
            # Step 2: First pass - validate structure and collect data
            rows_data = []
            row_count = 0
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
                row_count += 1
                
                # Normalize and validate SKU
                sku = self._normalize_string(row.get(sku_column, "").strip())
                name = self._normalize_string(row.get(name_column, "").strip())
                
                if not sku or not name:
                    validation_errors.append(f"Row {row_num}: Missing SKU or name")
                    continue
                
                # Check for duplicate SKUs within the file
                if sku in processed_skus:
                    duplicate_skus.add(sku)
                    validation_errors.append(f"Row {row_num}: Duplicate SKU '{sku}' found in CSV")
                    continue
                
                processed_skus.add(sku)
                
                # Validate and parse quantity
                try:
                    on_hand_str = row.get(on_hand_column, "0").strip()
                    on_hand = int(float(on_hand_str)) if on_hand_str else 0
                    if on_hand < 0:
                        validation_errors.append(f"Row {row_num}: Quantity cannot be negative")
                        continue
                except (ValueError, TypeError):
                    validation_errors.append(f"Row {row_num}: Invalid quantity value '{row.get(on_hand_column, '')}'")
                    continue
                
                # Validate and parse cost
                cost = 0.0
                if cost_column and cost_column in row and row.get(cost_column, "").strip():
                    try:
                        cost_str = row.get(cost_column, "0").strip()
                        cost = float(cost_str) if cost_str else 0.0
                        if cost < 0:
                            warnings.append(f"Row {row_num}: Negative cost for SKU '{sku}', using 0")
                            cost = 0.0
                    except (ValueError, TypeError):
                        warnings.append(f"Row {row_num}: Invalid cost value for SKU '{sku}', using 0")
                        cost = 0.0
                
                # Get variant if provided
                variant = None
                if variant_column and variant_column in row:
                    variant = self._normalize_string(row.get(variant_column, "").strip()) or None
                
                # Get supplier name
                supplier_name = None
                if supplier_name_column and supplier_name_column in row:
                    supplier_name = self._normalize_string(row.get(supplier_name_column, "").strip()) or None
                
                rows_data.append({
                    'row_num': row_num,
                    'sku': sku,
                    'name': name,
                    'variant': variant,
                    'on_hand': on_hand,
                    'cost': cost,
                    'supplier_name': supplier_name
                })
            
            # Check if we have too many validation errors
            if len(validation_errors) > 50:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Too many validation errors ({len(validation_errors)}). Please fix your CSV and try again."
                )
            
            # Step 3: Process valid rows
            for row_data in rows_data:
                try:
                    # Handle supplier
                    supplier_id = None
                    if row_data['supplier_name']:
                        supplier = self._get_or_create_supplier(row_data['supplier_name'], user_id)
                        supplier_id = supplier.id
                    
                    # Update or create product
                    result = await self._update_or_create_product(
                        sku=row_data['sku'],
                        name=row_data['name'],
                        variant=row_data['variant'],
                        on_hand=row_data['on_hand'],
                        cost=row_data['cost'],
                        supplier_id=supplier_id,
                        user_id=user_id,
                        source="csv",
                        reference_id=f"csv_import_{datetime.utcnow().isoformat()}"
                    )
                    
                    imported_items += 1
                    if result["created"]:
                        created_items += 1
                    else:
                        updated_items += 1
                    
                    # Track products that need threshold evaluation
                    threshold_updates.append(result["product"])
                        
                except Exception as e:
                    errors.append(f"Row {row_data['row_num']}: {str(e)}")
                    continue
            
            # Step 4: Run threshold engine for updated products
            await self._run_threshold_engine(threshold_updates)
            
            # Step 5: Generate alerts for low stock items
            await self._generate_stock_alerts(threshold_updates, user_id)
            
            # Step 6: Create audit log entry
            await self._create_audit_log(
                user_id=user_id,
                action=AuditAction.CSV_IMPORT,
                details={
                    "filename": file.filename,
                    "rows_processed": row_count,
                    "items_imported": imported_items,
                    "items_created": created_items,
                    "items_updated": updated_items,
                    "errors_count": len(errors),
                    "warnings_count": len(warnings)
                }
            )
            
            # Combine validation errors with processing errors
            all_errors = validation_errors + errors
            
        except Exception as e:
            logger.error(f"CSV import error: {str(e)}")
            # Create audit log for failed import
            if user_id:
                await self._create_audit_log(
                    user_id=user_id,
                    action=AuditAction.CSV_IMPORT,
                    details={
                        "filename": file.filename,
                        "status": "failed",
                        "error": str(e)
                    }
                )
            raise HTTPException(status_code=400, detail=f"CSV processing error: {str(e)}")
        
        return CSVUploadResponse(
            imported_items=imported_items,
            updated_items=updated_items,
            created_items=created_items,
            errors=all_errors,
            warnings=warnings
        )
    
    def _normalize_string(self, value: str) -> str:
        """Normalize string values (trim, case, etc.)"""
        if not value:
            return ""
        # Trim whitespace and normalize case for names/suppliers
        return value.strip()
    
    def _get_or_create_supplier(self, supplier_name: str, user_id: Optional[UUID] = None) -> Supplier:
        """Get existing supplier or create new one with user_id and organization_id"""
        
        # Get user's organization_id
        organization_id = None
        if user_id:
            from app.models.data_models.User import User
            user = self.db.exec(select(User).where(User.id == user_id)).first()
            if user:
                organization_id = user.organization_id
        
        # First check if supplier exists within the organization
        supplier = None
        if organization_id:
            supplier = self.db.exec(
                select(Supplier).where(
                    (Supplier.name == supplier_name) & 
                    (Supplier.organization_id == organization_id)
                )
            ).first()
        elif user_id:
            # Fallback to user_id if no organization_id
            supplier = self.db.exec(
                select(Supplier).where(
                    (Supplier.name == supplier_name) & 
                    (Supplier.user_id == user_id)
                )
            ).first()
        
        # If not found and no user_id, check globally (for backward compatibility)
        if not supplier and not user_id:
            supplier = self.db.exec(
                select(Supplier).where(Supplier.name == supplier_name)
            ).first()
        
        if not supplier:
            # Create new supplier with basic info
            supplier_data = {
                "name": supplier_name,
                "contact_email": f"{supplier_name.lower().replace(' ', '').replace('.', '')}@example.com"
            }
            
            # Set user_id and organization_id if provided
            if user_id:
                supplier_data["user_id"] = user_id
            if organization_id:
                supplier_data["organization_id"] = organization_id
            
            supplier = Supplier(**supplier_data)
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            logger.info(f"Created new supplier: {supplier_name} for organization {organization_id}")
        
        return supplier
    
    async def _run_threshold_engine(self, products: List[Product]):
        """Run threshold calculations for updated products"""
        for product in products:
            try:
                # Simple threshold calculation (can be enhanced)
                if product.reorder_point is None:
                    # Set default reorder point to 20% of current stock or minimum 5
                    product.reorder_point = max(int(product.on_hand * 0.2), 5)
                
                if product.safety_stock is None:
                    # Set safety stock to 10% of current stock or minimum 3
                    product.safety_stock = max(int(product.on_hand * 0.1), 3)
                
                self.db.add(product)
                logger.info(f"Updated thresholds for product {product.sku}: reorder={product.reorder_point}, safety={product.safety_stock}")
                
            except Exception as e:
                logger.error(f"Error updating thresholds for product {product.sku}: {str(e)}")
        
        self.db.commit()
    
    async def _generate_stock_alerts(self, products: List[Product], user_id: Optional[UUID]):
        """Generate alerts for products that need reordering"""
        for product in products:
            try:
                if product.reorder_point and product.on_hand <= product.reorder_point:
                    # Check if alert already exists for this product
                    existing_alert = self.db.exec(
                        select(Alert).where(
                            Alert.product_id == product.id,
                            Alert.alert_type == AlertType.LOW_STOCK,
                            Alert.is_resolved == False
                        )
                    ).first()
                    
                    if not existing_alert:
                        # Calculate estimated days of stock
                        days_left = self._calculate_days_of_stock(product)
                        
                        alert = Alert(
                            alert_type=AlertType.LOW_STOCK,
                            product_id=product.id,
                            message=f"Reorder {product.reorder_point - product.on_hand + product.safety_stock} units of '{product.name}' (SKU: {product.sku}) – only {days_left} days of stock left",
                            severity="high" if product.on_hand <= (product.safety_stock or 0) else "medium",
                            created_by=user_id
                        )
                        self.db.add(alert)
                        logger.info(f"Created low stock alert for product {product.sku}")
                        
            except Exception as e:
                logger.error(f"Error generating alert for product {product.sku}: {str(e)}")
        
        self.db.commit()
    
    def _calculate_days_of_stock(self, product: Product) -> int:
        """Calculate estimated days of stock remaining"""
        # Simple calculation - can be enhanced with historical sales data
        # For now, assume average daily usage is 10% of reorder point
        if product.reorder_point and product.reorder_point > 0:
            daily_usage = max(product.reorder_point * 0.1, 1)
            return max(int(product.on_hand / daily_usage), 0)
        return 0
    
    async def _create_audit_log(self, user_id: Optional[UUID], action: AuditAction, details: Dict[str, Any]):
        """Create audit log entry for SOC-2 compliance"""
        if user_id:
            try:
                audit_entry = AuditLog(
                    user_id=user_id,
                    action=action,
                    details=details,
                    timestamp=datetime.utcnow()
                )
                self.db.add(audit_entry)
                self.db.commit()
                logger.info(f"Created audit log entry for user {user_id}: {action}")
            except Exception as e:
                logger.error(f"Error creating audit log: {str(e)}")
    
    async def test_connection(self, connector_id: UUID) -> ConnectorTestResponse:
        """Test connector connection"""
        connector = self.db.exec(select(Connector).where(Connector.id == connector_id)).first()
        if not connector:
            raise HTTPException(status_code=404, detail="Connector not found")
        
        try:
            if connector.provider == ConnectorProvider.SHOPIFY:
                return await self._test_shopify_connection(connector)
            elif connector.provider == ConnectorProvider.SQUARE:
                return await self._test_square_connection(connector)
            elif connector.provider == ConnectorProvider.LIGHTSPEED:
                return await self._test_lightspeed_connection(connector)
            else:
                return ConnectorTestResponse(
                    provider=connector.provider,
                    status="ERROR",
                    connection_valid=False,
                    error_message="Unsupported provider"
                )
        except Exception as e:
            logger.error(f"Connection test error: {str(e)}")
            return ConnectorTestResponse(
                provider=connector.provider,
                status="ERROR",
                connection_valid=False,
                error_message=str(e)
            )
    
    async def _test_shopify_connection(self, connector: Connector) -> ConnectorTestResponse:
        """Test Shopify connection"""
        headers = {
            "X-Shopify-Access-Token": connector.access_token,
            "Content-Type": "application/json"
        }
        
        shop_domain = connector.config.get("shop_domain") if connector.config else None
        if not shop_domain:
            return ConnectorTestResponse(
                provider=ConnectorProvider.SHOPIFY,
                status="ERROR",
                connection_valid=False,
                error_message="Shop domain not configured"
            )
        
        # Use the latest API version and test with shop info endpoint
        url = f"https://{shop_domain}/admin/api/2025-01/shop.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    shop_info = data.get("shop", {})
                    return ConnectorTestResponse(
                        provider=ConnectorProvider.SHOPIFY,
                        status="ACTIVE",
                        connection_valid=True,
                        test_data={
                            "shop_name": shop_info.get("name"),
                            "shop_domain": shop_info.get("domain"),
                            "primary_location_id": shop_info.get("primary_location_id"),
                            "currency": shop_info.get("currency")
                        }
                    )
                else:
                    error_text = await response.text()
                    return ConnectorTestResponse(
                        provider=ConnectorProvider.SHOPIFY,
                        status="ERROR",
                        connection_valid=False,
                        error_message=f"API error: {error_text}"
                    )
    
    async def _test_square_connection(self, connector: Connector) -> ConnectorTestResponse:
        """Test Square connection"""
        headers = {
            "Authorization": f"Bearer {connector.access_token}",
            "Content-Type": "application/json",
            "Square-Version": "2025-04-16"
        }
        
        url = "https://connect.squareup.com/v2/locations"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    locations = data.get("locations", [])
                    return ConnectorTestResponse(
                        provider=ConnectorProvider.SQUARE,
                        status="ACTIVE",
                        connection_valid=True,
                        test_data={
                            "locations_count": len(locations),
                            "first_location": locations[0].get("name") if locations else None
                        }
                    )
                else:
                    error_text = await response.text()
                    return ConnectorTestResponse(
                        provider=ConnectorProvider.SQUARE,
                        status="ERROR",
                        connection_valid=False,
                        error_message=f"API error: {error_text}"
                    )
    
    async def _test_lightspeed_connection(self, connector: Connector) -> ConnectorTestResponse:
        """Test Lightspeed connection"""
        account_id = connector.config.get("account_id") if connector.config else None
        if not account_id:
            return ConnectorTestResponse(
                provider=ConnectorProvider.LIGHTSPEED,
                status="ERROR",
                connection_valid=False,
                error_message="Account ID not configured"
            )
        
        headers = {
            "Authorization": f"Bearer {connector.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.lightspeedapp.com/API/Account/{account_id}.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    account_info = data.get("Account", {})
                    return ConnectorTestResponse(
                        provider=ConnectorProvider.LIGHTSPEED,
                        status="ACTIVE",
                        connection_valid=True,
                        test_data={
                            "account_name": account_info.get("name"),
                            "account_id": account_info.get("accountID")
                        }
                    )
                else:
                    error_text = await response.text()
                    return ConnectorTestResponse(
                        provider=ConnectorProvider.LIGHTSPEED,
                        status="ERROR",
                        connection_valid=False,
                        error_message=f"API error: {error_text}"
                    )
    
    async def _update_or_create_product(
        self,
        sku: str,
        name: str,
        on_hand: int,
        cost: float = 0.0,
        variant: Optional[str] = None,
        supplier_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        source: str = "manual",
        reference_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update existing product or create new one with user_id and organization_id"""
        
        # Get user's organization_id
        organization_id = None
        if user_id:
            from app.models.data_models.User import User
            user = self.db.exec(select(User).where(User.id == user_id)).first()
            if user:
                organization_id = user.organization_id
        
        # Check if product exists within the organization (not just by user_id)
        if organization_id:
            existing_product = self.db.exec(
                select(Product).where(
                    (Product.sku == sku) & 
                    (Product.organization_id == organization_id)
                )
            ).first()
        elif user_id:
            # Fallback to user_id if no organization_id
            existing_product = self.db.exec(
                select(Product).where(
                    (Product.sku == sku) & 
                    (Product.user_id == user_id)
                )
            ).first()
        else:
            # For backward compatibility, check globally if no user_id
            existing_product = self.db.exec(select(Product).where(Product.sku == sku)).first()
        
        if existing_product:
            # Update existing product
            old_quantity = existing_product.on_hand
            quantity_delta = on_hand - old_quantity
            
            existing_product.on_hand = on_hand
            existing_product.cost = cost
            if variant:
                existing_product.variant = variant
            if supplier_id:
                existing_product.supplier_id = supplier_id
            
            # Ensure organization_id is set if missing
            if organization_id and not existing_product.organization_id:
                existing_product.organization_id = organization_id
            
            self.db.add(existing_product)
            
            # Create ledger entry for the change
            if quantity_delta != 0:
                ledger_entry = InventoryLedger(
                    product_id=existing_product.id,
                    quantity_delta=quantity_delta,
                    quantity_after=on_hand,
                    source=source,
                    reference_id=reference_id
                )
                self.db.add(ledger_entry)
            
            self.db.commit()
            return {"created": False, "product": existing_product}
        
        else:
            # Create new product
            product_data = {
                "sku": sku,
                "name": name,
                "variant": variant,
                "on_hand": on_hand,
                "cost": cost,
                "supplier_id": supplier_id
            }
            
            # Set user_id and organization_id if provided
            if user_id:
                product_data["user_id"] = user_id
            if organization_id:
                product_data["organization_id"] = organization_id
            
            new_product = Product(**product_data)
            
            self.db.add(new_product)
            self.db.commit()
            self.db.refresh(new_product)
            
            # Create initial ledger entry
            ledger_entry = InventoryLedger(
                product_id=new_product.id,
                quantity_delta=on_hand,
                quantity_after=on_hand,
                source=source,
                reference_id=reference_id
            )
            self.db.add(ledger_entry)
            self.db.commit()
            
            return {"created": True, "product": new_product}
    
    async def initialize_shopify_oauth(self, shop_domain: str, oauth_code: str, user_id: UUID) -> Connector:
        """
        Initialize Shopify connector using OAuth code exchange.
        This handles the initial OAuth flow after user grants permissions.
        """
        try:
            # Get user's organization_id
            from app.models.data_models.User import User
            user = self.db.exec(select(User).where(User.id == user_id)).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            organization_id = user.organization_id
            
            # Shopify OAuth token exchange
            token_url = f"https://{shop_domain}/admin/oauth/access_token"
            
            client_id = os.environ.get("SHOPIFY_CLIENT_ID")
            client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                raise HTTPException(
                    status_code=500, 
                    detail="Shopify OAuth credentials not configured"
                )
            
            payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": oauth_code
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=400,
                            detail=f"Shopify OAuth error: {error_text}"
                        )
                    
                    token_data = await response.json()
                    access_token = token_data.get("access_token")
                    scope = token_data.get("scope")
                    
                    if not access_token:
                        raise HTTPException(
                            status_code=400,
                            detail="Failed to obtain access token from Shopify"
                        )
            
            # Create connector with PENDING status and organization_id
            connector = Connector(
                provider=ConnectorProvider.SHOPIFY,
                access_token=access_token,
                config={
                    "shop_domain": shop_domain,
                    "scope": scope
                },
                created_by=user_id,
                organization_id=organization_id,
                status="PENDING"
            )
            
            self.db.add(connector)
            self.db.commit()
            self.db.refresh(connector)
            
            # Test the connection immediately
            test_result = await self._test_shopify_connection(connector)
            if test_result.connection_valid:
                connector.status = "ACTIVE"
                self.db.add(connector)
                self.db.commit()
                
                # Trigger initial sync
                await self.sync_shopify(connector.id)
            else:
                connector.status = "ERROR"
                self.db.add(connector)
                self.db.commit()
                
            return connector
            
        except Exception as e:
            logger.error(f"Shopify OAuth initialization error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def initialize_square_oauth(self, oauth_code: str, user_id: UUID) -> Connector:
        """
        Initialize Square connector using OAuth code exchange.
        """
        try:
            # Get user's organization_id
            from app.models.data_models.User import User
            user = self.db.exec(select(User).where(User.id == user_id)).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            organization_id = user.organization_id
            
            # Square OAuth token exchange
            token_url = "https://connect.squareup.com/oauth2/token"
            
            client_id = os.environ.get("SQUARE_CLIENT_ID")
            client_secret = os.environ.get("SQUARE_CLIENT_SECRET")
            redirect_uri = os.environ.get("SQUARE_REDIRECT_URI")
            
            if not client_id or not client_secret:
                raise HTTPException(
                    status_code=500,
                    detail="Square OAuth credentials not configured"
                )
            
            payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": oauth_code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Square-Version": "2025-04-16"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=400,
                            detail=f"Square OAuth error: {error_text}"
                        )
                    
                    token_data = await response.json()
                    access_token = token_data.get("access_token")
                    refresh_token = token_data.get("refresh_token")
                    expires_at = token_data.get("expires_at")
                    
                    if not access_token:
                        raise HTTPException(
                            status_code=400,
                            detail="Failed to obtain access token from Square"
                        )
            
            # Create connector with organization_id
            connector = Connector(
                provider=ConnectorProvider.SQUARE,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=datetime.fromisoformat(expires_at.replace('Z', '+00:00')) if expires_at else None,
                config={
                    "merchant_id": token_data.get("merchant_id")
                },
                created_by=user_id,
                organization_id=organization_id,
                status="PENDING"
            )
            
            self.db.add(connector)
            self.db.commit()
            self.db.refresh(connector)
            
            # Test connection and activate
            test_result = await self._test_square_connection(connector)
            if test_result.connection_valid:
                connector.status = "ACTIVE"
                self.db.add(connector)
                self.db.commit()
                
                # Trigger initial sync
                await self.sync_square(connector.id)
            else:
                connector.status = "ERROR"
                self.db.add(connector)
                self.db.commit()
                
            return connector
            
        except Exception as e:
            logger.error(f"Square OAuth initialization error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def initialize_lightspeed_oauth(self, oauth_code: str, user_id: UUID) -> Connector:
        """
        Initialize Lightspeed connector using OAuth code exchange.
        """
        try:
            # Lightspeed OAuth token exchange
            token_url = "https://cloud.lightspeedapp.com/oauth/access_token.php"
            
            client_id = os.environ.get("LIGHTSPEED_CLIENT_ID")
            client_secret = os.environ.get("LIGHTSPEED_CLIENT_SECRET")
            redirect_uri = os.environ.get("LIGHTSPEED_REDIRECT_URI")
            
            if not client_id or not client_secret:
                raise HTTPException(
                    status_code=500,
                    detail="Lightspeed OAuth credentials not configured"
                )
            
            payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": oauth_code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=400,
                            detail=f"Lightspeed OAuth error: {error_text}"
                        )
                    
                    token_data = await response.json()
                    access_token = token_data.get("access_token")
                    refresh_token = token_data.get("refresh_token")
                    
                    if not access_token:
                        raise HTTPException(
                            status_code=400,
                            detail="Failed to obtain access token from Lightspeed"
                        )
            
            # Get account information
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.lightspeedapp.com/API/Account.json", headers=headers) as response:
                    if response.status == 200:
                        account_data = await response.json()
                        account_info = account_data.get("Account", {})
                        account_id = account_info.get("accountID")
                    else:
                        account_id = None
            
            # Create connector
            connector = Connector(
                provider=ConnectorProvider.LIGHTSPEED,
                access_token=access_token,
                refresh_token=refresh_token,
                config={
                    "account_id": account_id
                },
                created_by=user_id,
                status="PENDING"
            )
            
            self.db.add(connector)
            self.db.commit()
            self.db.refresh(connector)
            
            # Test connection and activate
            test_result = await self._test_lightspeed_connection(connector)
            if test_result.connection_valid:
                connector.status = "ACTIVE"
                self.db.add(connector)
                self.db.commit()
                
                # Trigger initial sync
                await self.sync_lightspeed(connector.id)
            else:
                connector.status = "ERROR"
                self.db.add(connector)
                self.db.commit()
                
            return connector
            
        except Exception as e:
            logger.error(f"Lightspeed OAuth initialization error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e)) 