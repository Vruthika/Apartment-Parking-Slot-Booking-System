from sqlalchemy.orm import Session
from app.models.request import Request
from app.models.user import User
from app.models.slot import Slot
from app.schemas.request_schema import RequestCreate, RequestUpdate
from fastapi import HTTPException, status
from datetime import datetime

def get_request_by_id(db: Session, request_id: int):
    return db.query(Request).filter(Request.id == request_id).first()

def get_all_requests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Request).offset(skip).limit(limit).all()

def get_pending_requests(db: Session):
    return db.query(Request).filter(Request.status == "pending").all()

def get_requests_by_type(db: Session, request_type: str):
    return db.query(Request).filter(Request.request_type == request_type).all()

def create_request(db: Session, request: RequestCreate):
    # Check if resident exists
    resident = db.query(User).filter(User.id == request.resident_id, User.role == "resident").first()
    if not resident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resident not found"
        )
    
    # Check if slot exists
    slot = db.query(Slot).filter(Slot.id == request.slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found"
        )
    
    db_request = Request(
        request_type=request.request_type,
        description=request.description,
        status="pending",
        resident_id=request.resident_id,
        slot_id=request.slot_id
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def update_request_status(db: Session, request_id: int, status: str):
    db_request = get_request_by_id(db, request_id)
    if not db_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    db_request.status = status
    
    # If it's a damage report and approved, mark slot as damaged
    if db_request.request_type == "damage_report" and status == "approved":
        slot = db.query(Slot).filter(Slot.id == db_request.slot_id).first()
        if slot:
            slot.status = "damaged"
    
    db.commit()
    db.refresh(db_request)
    return db_request