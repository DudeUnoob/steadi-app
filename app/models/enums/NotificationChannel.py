from enum import Enum

class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"
    SMS = "SMS"