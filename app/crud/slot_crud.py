from sqlalchemy.orm import Session
from app.models.slot import Slot
from app.schemas.slot_schema import SlotCreate, SlotUpdate
from fastapi import HTTPException, status

def get_slot_by_id(db: Session, slot_id: int):
    return db.query(Slot).filter(Slot.id == slot_id).first()

def get_slot_by_number(db: Session, slot_number: str):
    return db.query(Slot).filter(Slot.slot_number == slot_number).first()

def get_all_slots(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Slot).offset(skip).limit(limit).all()

def get_slots_by_status(db: Session, status: str):
    return db.query(Slot).filter(Slot.status == status).all()

def get_slots_by_type(db: Session, slot_type: str):
    return db.query(Slot).filter(Slot.slot_type == slot_type).all()

def create_slot(db: Session, slot: SlotCreate):
    # Check if slot number already exists
    db_slot = get_slot_by_number(db, slot.slot_number)
    if db_slot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot number already exists"
        )
    
    db_slot = Slot(
        slot_number=slot.slot_number,
        slot_type=slot.slot_type,
        status=slot.status
    )
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot

def update_slot(db: Session, slot_id: int, slot_update: SlotUpdate):
    db_slot = get_slot_by_id(db, slot_id)
    if not db_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found"
        )
    
    update_data = slot_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_slot, field, value)
    
    db.commit()
    db.refresh(db_slot)
    return db_slot

def delete_slot(db: Session, slot_id: int):
    db_slot = get_slot_by_id(db, slot_id)
    if not db_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found"
        )
    
    db.delete(db_slot)
    db.commit()
    return {"message": "Slot deleted successfully"}