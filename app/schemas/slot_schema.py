from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SlotBase(BaseModel):
    slot_number: str
    slot_type: str  # "two_wheeler" or "four_wheeler"
    status: str = "available"  # available, occupied, reserved, damaged

class SlotCreate(SlotBase):
    pass

class SlotUpdate(BaseModel):
    slot_number: Optional[str] = None
    slot_type: Optional[str] = None
    status: Optional[str] = None

class SlotResponse(SlotBase):
    id: int
    assigned_resident_id: Optional[int] = None
    assigned_resident_name: Optional[str] = None

    class Config:
        from_attributes = True