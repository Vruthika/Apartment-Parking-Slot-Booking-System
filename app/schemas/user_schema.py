from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    flat_number: Optional[str] = None
    phone_number: Optional[str] = None
    vehicle_type: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    flat_number: Optional[str]
    phone_number: Optional[str]
    vehicle_type: Optional[str]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str