from uuid import UUID
from typing import Dict

class ConnectorService:
    """Manages external system connections and synchronization"""
    
    def sync_shopify(self, connector_id: UUID) -> Dict:
        """Sync inventory from Shopify"""
        pass
    
    def sync_square(self, connector_id: UUID) -> Dict:
        """Sync inventory from Square"""
        pass
    
    def sync_lightspeed(self, connector_id: UUID) -> Dict:
        """Sync inventory from Lightspeed"""
        pass
    
    def import_csv(self, file_path: str, mapping: Dict) -> Dict:
        """Import inventory from CSV file"""
        pass

