from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VisitorBase(BaseModel):
    visitor_name: str
    vehicle_number: str
    vehicle_type: str
    entry_time: datetime
    exit_time: Optional[datetime] = None

class VisitorCreate(VisitorBase):
    resident_id: int

class VisitorUpdate(BaseModel):
    status: Optional[str] = None
    slot_id: Optional[int] = None
    exit_time: Optional[datetime] = None

class VisitorResponse(VisitorBase):
    id: int
    status: str
    resident_id: int
    resident_name: Optional[str] = None
    slot_id: Optional[int] = None
    slot_number: Optional[str] = None

    class Config:
        from_attributes = True