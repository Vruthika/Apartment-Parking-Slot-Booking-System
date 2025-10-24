from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.dependencies.auth import get_current_resident
from app.models.user import User
from app.models.slot import Slot
from app.models.visitor import Visitor

router = APIRouter()

@router.get("/slots")
def get_my_slots(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    # Return slots assigned to current resident
    if current_user.assigned_slot_id:
        slot = db.query(Slot).filter(Slot.id == current_user.assigned_slot_id).first()
        return [slot] if slot else []
    return []

@router.get("/visitors")
def get_my_visitors(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    # Return visitors for current resident
    visitors = db.query(Visitor).filter(Visitor.resident_id == current_user.id).all()
    return visitors

@router.post("/visitors")
def book_visitor_slot(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    return {"message": f"Visitor booking for resident {current_user.full_name}"}

@router.post("/requests")
def create_request(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    return {"message": f"Request created by resident {current_user.full_name}"}