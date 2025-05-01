from enum import Enum

class ConnectorProvider(str, Enum):
    SHOPIFY = "SHOPIFY"
    SQUARE = "SQUARE"
    LIGHTSPEED = "LIGHTSPEED"
    CSV = "CSV"
