from sqlalchemy.orm import Session
from app.models.visitor import Visitor
from app.models.user import User
from app.models.slot import Slot
from app.schemas.visitor_schema import VisitorCreate, VisitorUpdate
from fastapi import HTTPException, status
from datetime import datetime

def get_visitor_by_id(db: Session, visitor_id: int):
    return db.query(Visitor).filter(Visitor.id == visitor_id).first()

def get_all_visitors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Visitor).offset(skip).limit(limit).all()

def get_pending_visitors(db: Session):
    return db.query(Visitor).filter(Visitor.status == "pending").all()

def get_visitors_by_resident(db: Session, resident_id: int):
    return db.query(Visitor).filter(Visitor.resident_id == resident_id).all()

def create_visitor(db: Session, visitor: VisitorCreate):
    # Check if resident exists
    resident = db.query(User).filter(User.id == visitor.resident_id, User.role == "resident").first()
    if not resident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resident not found"
        )
    
    db_visitor = Visitor(
        visitor_name=visitor.visitor_name,
        vehicle_number=visitor.vehicle_number,
        vehicle_type=visitor.vehicle_type,
        entry_time=visitor.entry_time,
        exit_time=visitor.exit_time,
        resident_id=visitor.resident_id,
        status="pending"
    )
    db.add(db_visitor)
    db.commit()
    db.refresh(db_visitor)
    return db_visitor

def update_visitor_status(db: Session, visitor_id: int, status: str, slot_id: int = None):
    db_visitor = get_visitor_by_id(db, visitor_id)
    if not db_visitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visitor not found"
        )
    
    db_visitor.status = status
    if slot_id:
        db_visitor.slot_id = slot_id
    
    db.commit()
    db.refresh(db_visitor)
    return db_visitor

def mark_visitor_exit(db: Session, visitor_id: int):
    db_visitor = get_visitor_by_id(db, visitor_id)
    if not db_visitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visitor not found"
        )
    
    db_visitor.exit_time = datetime.now()
    db_visitor.status = "completed"
    
    # Free up the slot if assigned
    if db_visitor.slot_id:
        slot = db.query(Slot).filter(Slot.id == db_visitor.slot_id).first()
        if slot:
            slot.status = "available"
    
    db.commit()
    return db_visitor

def get_pending_visitors(db: Session):
    """Get all visitors with pending status (unplanned visitors waiting approval)"""
    return db.query(Visitor).filter(Visitor.status == "pending").all()