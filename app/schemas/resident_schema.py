from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResidentProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    vehicle_type: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class SlotChangeRequest(BaseModel):
    reason: str
    preferred_slot_type: Optional[str] = None

class DamageReport(BaseModel):
    description: str
    # For future: image_url: Optional[str] = None

class VisitorBooking(BaseModel):
    visitor_name: str
    vehicle_number: str
    vehicle_type: str
    entry_time: datetime
    exit_time: Optional[datetime] = None

class ResidentDashboard(BaseModel):
    assigned_slot: Optional[dict]
    active_visitors: list
    pending_requests: list
    notifications_count: int

class Notification(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True