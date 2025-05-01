from uuid import UUID
from typing import Dict, List
from app.models.data_models.PurchaseOrder import PurchaseOrder
from app.models.enums.POStatus import POStatus

class PurchaseOrderService:
    """Manages purchase order creation and workflow"""
    
    def create_purchase_order(self, supplier_id: UUID, lines: List[Dict], send_email: bool = False) -> PurchaseOrder:
        """Create a purchase order with optional email"""
        pass
    
    def generate_pdf(self, purchase_order_id: UUID) -> str:
        """Generate PDF for purchase order"""
        pass
    
    def update_status(self, purchase_order_id: UUID, status: POStatus) -> PurchaseOrder:
        """Update purchase order status"""
        pass
