from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    RESIDENT = "resident"

class SlotStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    DAMAGED = "damaged"

class VehicleType(str, Enum):
    TWO_WHEELER = "two_wheeler"
    FOUR_WHEELER = "four_wheeler"

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class VisitorStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"