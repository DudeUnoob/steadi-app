from enum import Enum

class UserRole(str, Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    
    def __str__(self):
        return self.value
