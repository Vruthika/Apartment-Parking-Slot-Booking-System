from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RequestBase(BaseModel):
    request_type: str  # "slot_change", "damage_report"
    description: str
    slot_id: int

class RequestCreate(RequestBase):
    resident_id: int

class RequestUpdate(BaseModel):
    status: Optional[str] = None

class RequestResponse(RequestBase):
    id: int
    status: str
    resident_id: int
    resident_name: Optional[str] = None
    slot_number: Optional[str] = None

    class Config:
        from_attributes = True