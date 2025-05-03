from enum import Enum

class POStatus(str, Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    RECEIVED = "RECEIVED"

