from sqlalchemy import Column, Integer, String
from app.config.database import Base
from sqlalchemy.orm import relationship

class Slot(Base):
    __tablename__ = "slots"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_number = Column(String, unique=True, index=True)
    slot_type = Column(String)  # "two_wheeler" or "four_wheeler"
    status = Column(String, default="available")  # available, occupied, reserved, damaged
    
    # Relationships
    residents = relationship("User", backref="assigned_slot")
    visitors = relationship("Visitor", back_populates="assigned_slot")