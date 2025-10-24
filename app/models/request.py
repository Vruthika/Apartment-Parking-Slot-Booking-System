from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey
from app.config.database import Base
from sqlalchemy.orm import relationship

class Request(Base):
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String)  # "slot_change", "damage_report"
    description = Column(Text)
    status = Column(String, default="pending")  # pending, approved, rejected, completed
    resident_id = Column(Integer, ForeignKey("users.id"))
    slot_id = Column(Integer, ForeignKey("slots.id"))
    
    # Relationships
    resident = relationship("User", back_populates="requests")