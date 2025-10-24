from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String)  # "admin" or "resident"
    flat_number = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)  # "two_wheeler" or "four_wheeler"
    
    assigned_slot_id = Column(Integer, ForeignKey("slots.id"), nullable=True)
    
    # Relationships
    visitors = relationship("Visitor", back_populates="resident")
    requests = relationship("Request", back_populates="resident")