from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base

class Visitor(Base):
    __tablename__ = "visitors"
    
    id = Column(Integer, primary_key=True, index=True)
    visitor_name = Column(String)
    vehicle_number = Column(String)
    vehicle_type = Column(String)
    entry_time = Column(DateTime)
    exit_time = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected, completed
    resident_id = Column(Integer, ForeignKey("users.id"))
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=True)
    
    # Relationships
    resident = relationship("User", back_populates="visitors")
    assigned_slot = relationship("Slot", back_populates="visitors")