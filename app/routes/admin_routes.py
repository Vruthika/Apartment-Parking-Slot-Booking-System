from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.user import User
from app.models.slot import Slot
from app.models.visitor import Visitor
from app.models.request import Request

# Import schemas
from app.schemas.slot_schema import SlotCreate, SlotUpdate, SlotResponse
from app.schemas.visitor_schema import VisitorResponse, VisitorUpdate
from app.schemas.request_schema import RequestResponse, RequestUpdate
from app.schemas.user_schema import UserResponse, UserCreate

# Import CRUD operations
from app.crud import user_crud, slot_crud, visitor_crud, request_crud

router = APIRouter()

# ========== USER/RESIDENT MANAGEMENT ==========

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all users (both admin and residents)"""
    return db.query(User).all()

@router.get("/residents", response_model=List[UserResponse])
def get_all_residents(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all residents only"""
    return db.query(User).filter(User.role == "resident").all()

@router.post("/residents", response_model=UserResponse)
def create_resident(
    resident: UserCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new resident"""
    resident.role = "resident"  # Force role to resident
    return user_crud.create_user(db, resident)

@router.put("/residents/{resident_id}/assign-slot")
def assign_slot_to_resident(
    resident_id: int,
    slot_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Assign a parking slot to a resident"""
    resident = db.query(User).filter(User.id == resident_id, User.role == "resident").first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    # Check if slot is available
    if slot.status != "available":
        raise HTTPException(status_code=400, detail="Slot is not available")
    
    # Assign slot to resident
    resident.assigned_slot_id = slot_id
    slot.status = "occupied"
    
    db.commit()
    return {"message": f"Slot {slot.slot_number} assigned to resident {resident.full_name}"}

@router.delete("/residents/{resident_id}")
def delete_resident(
    resident_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a resident"""
    resident = db.query(User).filter(User.id == resident_id, User.role == "resident").first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    
    # Free up the assigned slot
    if resident.assigned_slot_id:
        slot = db.query(Slot).filter(Slot.id == resident.assigned_slot_id).first()
        if slot:
            slot.status = "available"
    
    db.delete(resident)
    db.commit()
    return {"message": "Resident deleted successfully"}

# ========== SLOT MANAGEMENT ==========

@router.get("/slots", response_model=List[SlotResponse])
def get_all_slots(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all parking slots"""
    slots = db.query(Slot).all()
    
    # Enhance response with resident info
    enhanced_slots = []
    for slot in slots:
        slot_data = SlotResponse.from_orm(slot)
        if slot.residents:  # Get the first resident assigned to this slot
            resident = slot.residents[0]
            slot_data.assigned_resident_id = resident.id
            slot_data.assigned_resident_name = resident.full_name
        enhanced_slots.append(slot_data)
    
    return enhanced_slots

@router.post("/slots", response_model=SlotResponse)
def create_slot(
    slot: SlotCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new parking slot"""
    return slot_crud.create_slot(db, slot)

@router.put("/slots/{slot_id}", response_model=SlotResponse)
def update_slot(
    slot_id: int,
    slot_update: SlotUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a parking slot"""
    return slot_crud.update_slot(db, slot_id, slot_update)

@router.delete("/slots/{slot_id}")
def delete_slot(
    slot_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a parking slot"""
    return slot_crud.delete_slot(db, slot_id)

@router.put("/slots/{slot_id}/mark-damaged")
def mark_slot_damaged(
    slot_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mark a slot as damaged"""
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    slot.status = "damaged"
    db.commit()
    return {"message": f"Slot {slot.slot_number} marked as damaged"}

@router.put("/slots/{slot_id}/mark-repaired")
def mark_slot_repaired(
    slot_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mark a damaged slot as repaired and available"""
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    slot.status = "available"
    db.commit()
    return {"message": f"Slot {slot.slot_number} marked as repaired and available"}

# ========== VISITOR MANAGEMENT ==========

@router.get("/visitors", response_model=List[VisitorResponse])
def get_all_visitors(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all visitor bookings"""
    visitors = db.query(Visitor).all()
    
    # Enhance response with resident and slot info
    enhanced_visitors = []
    for visitor in visitors:
        visitor_data = VisitorResponse.from_orm(visitor)
        
        # Get resident name
        resident = db.query(User).filter(User.id == visitor.resident_id).first()
        if resident:
            visitor_data.resident_name = resident.full_name
        
        # Get slot number if assigned
        if visitor.slot_id:
            slot = db.query(Slot).filter(Slot.id == visitor.slot_id).first()
            if slot:
                visitor_data.slot_number = slot.slot_number
        
        enhanced_visitors.append(visitor_data)
    
    return enhanced_visitors

@router.get("/visitors/pending", response_model=List[VisitorResponse])
def get_pending_visitors(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all pending visitor requests"""
    return visitor_crud.get_pending_visitors(db)

@router.put("/visitors/{visitor_id}/approve")
def approve_visitor(
    visitor_id: int,
    slot_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Approve a visitor request and assign a slot"""
    # Check if slot is available
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot or slot.status != "available":
        raise HTTPException(status_code=400, detail="Slot not available")
    
    # Approve visitor and assign slot
    visitor = visitor_crud.update_visitor_status(db, visitor_id, "approved", slot_id)
    
    # Mark slot as occupied
    slot.status = "occupied"
    db.commit()
    
    return {"message": f"Visitor approved and assigned slot {slot.slot_number}"}

@router.put("/visitors/{visitor_id}/reject")
def reject_visitor(
    visitor_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reject a visitor request"""
    visitor = visitor_crud.update_visitor_status(db, visitor_id, "rejected")
    return {"message": "Visitor request rejected"}

@router.put("/visitors/{visitor_id}/mark-exit")
def mark_visitor_exit(
    visitor_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mark visitor as exited and free up the slot"""
    visitor = visitor_crud.mark_visitor_exit(db, visitor_id)
    return {"message": "Visitor marked as exited"}

# ========== REQUEST MANAGEMENT ==========

@router.get("/requests", response_model=List[RequestResponse])
def get_all_requests(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all resident requests"""
    requests = db.query(Request).all()
    
    # Enhance response with resident and slot info
    enhanced_requests = []
    for req in requests:
        request_data = RequestResponse.from_orm(req)
        
        # Get resident name
        resident = db.query(User).filter(User.id == req.resident_id).first()
        if resident:
            request_data.resident_name = resident.full_name
        
        # Get slot number
        slot = db.query(Slot).filter(Slot.id == req.slot_id).first()
        if slot:
            request_data.slot_number = slot.slot_number
        
        enhanced_requests.append(request_data)
    
    return enhanced_requests

@router.get("/requests/pending", response_model=List[RequestResponse])
def get_pending_requests(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all pending requests"""
    return request_crud.get_pending_requests(db)

@router.get("/requests/damage-reports", response_model=List[RequestResponse])
def get_damage_reports(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all damage report requests"""
    return request_crud.get_requests_by_type(db, "damage_report")

@router.put("/requests/{request_id}/approve")
def approve_request(
    request_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Approve a resident request"""
    request = request_crud.update_request_status(db, request_id, "approved")
    return {"message": "Request approved"}

@router.put("/requests/{request_id}/reject")
def reject_request(
    request_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reject a resident request"""
    request = request_crud.update_request_status(db, request_id, "rejected")
    return {"message": "Request rejected"}

@router.put("/requests/{request_id}/complete")
def complete_request(
    request_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mark a request as completed"""
    request = request_crud.update_request_status(db, request_id, "completed")
    return {"message": "Request marked as completed"}

# ========== DASHBOARD SUMMARY ==========

@router.get("/summary")
def get_admin_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard summary"""
    total_slots = db.query(Slot).count()
    available_slots = db.query(Slot).filter(Slot.status == "available").count()
    occupied_slots = db.query(Slot).filter(Slot.status == "occupied").count()
    damaged_slots = db.query(Slot).filter(Slot.status == "damaged").count()
    
    total_residents = db.query(User).filter(User.role == "resident").count()
    pending_visitors = db.query(Visitor).filter(Visitor.status == "pending").count()
    pending_requests = db.query(Request).filter(Request.status == "pending").count()
    
    return {
        "total_slots": total_slots,
        "available_slots": available_slots,
        "occupied_slots": occupied_slots,
        "damaged_slots": damaged_slots,
        "total_residents": total_residents,
        "pending_visitors": pending_visitors,
        "pending_requests": pending_requests
    }