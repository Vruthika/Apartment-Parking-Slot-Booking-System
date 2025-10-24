from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from app.config.database import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(Text)
    type = Column(String)  # "visitor_approval", "slot_repair", "request_update"
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())