from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime

from app.config.database import get_db
from app.dependencies.auth import get_current_resident
from app.models.user import User
from app.models.slot import Slot
from app.models.visitor import Visitor
from app.models.request import Request
from app.models.notification import Notification

# Import schemas
from app.schemas.user_schema import UserResponse
from app.schemas.slot_schema import SlotResponse
from app.schemas.visitor_schema import VisitorCreate, VisitorResponse
from app.schemas.request_schema import RequestCreate, RequestResponse
from app.schemas.resident_schema import (
    ResidentProfileUpdate, PasswordChange, SlotChangeRequest,
    DamageReport, VisitorBooking, ResidentDashboard, Notification
)

# Import CRUD operations
from app.crud import user_crud, slot_crud, visitor_crud, request_crud, notification_crud
from app.utils.auth_utils import verify_password, get_password_hash
from app.websocket.manager import manager
from app.websocket.events import send_notification_to_resident, send_visitor_approval_request

router = APIRouter()

# ========== PROFILE MANAGEMENT ==========

@router.get("/profile", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Get resident's own profile"""
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_my_profile(
    profile_update: ResidentProfileUpdate,
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Update resident's profile"""
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Change resident's password"""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

# ========== SLOT MANAGEMENT ==========
router1 = APIRouter()
@router1.get("/my-slot", response_model=SlotResponse)
def get_my_slot(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Get resident's assigned parking slot"""
    if not current_user.assigned_slot_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No slot assigned"
        )
    
    slot = db.query(Slot).filter(Slot.id == current_user.assigned_slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned slot not found"
        )
    
    return slot

@router1.post("/slot/change-request")
def request_slot_change(
    change_request: SlotChangeRequest,
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Request to change assigned parking slot"""
    if not current_user.assigned_slot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No slot assigned to change"
        )
    
    # Create a slot change request
    db_request = Request(
        request_type="slot_change",
        description=f"Slot change request: {change_request.reason}. Preferred type: {change_request.preferred_slot_type}",
        status="pending",
        resident_id=current_user.id,
        slot_id=current_user.assigned_slot_id
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    # Create notification for admin (in real implementation, this would be via WebSocket)
    notification_crud.create_notification(
        db, 
        current_user.id,
        "Slot Change Request",
        f"Your slot change request has been submitted and is pending admin approval.",
        "request_submitted"
    )
    
    return {"message": "Slot change request submitted successfully", "request_id": db_request.id}

@router1.post("/slot/damage-report")
def report_slot_damage(
    damage_report: DamageReport,
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Report damage to assigned parking slot"""
    if not current_user.assigned_slot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No slot assigned to report damage"
        )
    
    # Create a damage report request
    db_request = Request(
        request_type="damage_report",
        description=f"Damage report: {damage_report.description}",
        status="pending",
        resident_id=current_user.id,
        slot_id=current_user.assigned_slot_id
    )
    db.add(db_request)
    
    # Mark slot as damaged
    slot = db.query(Slot).filter(Slot.id == current_user.assigned_slot_id).first()
    if slot:
        slot.status = "damaged"
    
    db.commit()
    db.refresh(db_request)
    
    # Notify resident
    notification_crud.create_notification(
        db, 
        current_user.id,
        "Damage Reported",
        "Your slot has been marked as damaged. Maintenance has been notified.",
        "damage_reported"
    )
    
    return {"message": "Damage reported successfully", "request_id": db_request.id}

# ========== VISITOR MANAGEMENT ==========
router2 = APIRouter()
@router2.post("/visitors", response_model=VisitorResponse)
def book_visitor_slot(
    visitor_booking: VisitorBooking,
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Book a parking slot for a visitor"""
    # Find available visitor slot
    available_slot = db.query(Slot).filter(
        Slot.slot_type == visitor_booking.vehicle_type,
        Slot.status == "available"
    ).first()
    
    if not available_slot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No available {visitor_booking.vehicle_type} slots for visitors"
        )
    
    # Create visitor booking
    db_visitor = Visitor(
        visitor_name=visitor_booking.visitor_name,
        vehicle_number=visitor_booking.vehicle_number,
        vehicle_type=visitor_booking.vehicle_type,
        entry_time=visitor_booking.entry_time,
        exit_time=visitor_booking.exit_time,
        resident_id=current_user.id,
        slot_id=available_slot.id,
        status="approved"  # Auto-approve for pre-booked visitors
    )
    
    # Mark slot as occupied
    available_slot.status = "occupied"
    
    db.add(db_visitor)
    db.commit()
    db.refresh(db_visitor)
    
    # Notify resident
    notification_crud.create_notification(
        db, 
        current_user.id,
        "Visitor Booking Confirmed",
        f"Visitor {visitor_booking.visitor_name} has been booked for slot {available_slot.slot_number}",
        "visitor_approved"
    )
    
    return db_visitor

@router2.get("/visitors", response_model=List[VisitorResponse])
def get_my_visitors(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Get all visitor bookings for the resident"""
    visitors = db.query(Visitor).filter(Visitor.resident_id == current_user.id).all()
    
    # Enhance response with slot info
    enhanced_visitors = []
    for visitor in visitors:
        visitor_data = VisitorResponse.from_orm(visitor)
        if visitor.slot_id:
            slot = db.query(Slot).filter(Slot.id == visitor.slot_id).first()
            if slot:
                visitor_data.slot_number = slot.slot_number
        enhanced_visitors.append(visitor_data)
    
    return enhanced_visitors

@router2.get("/visitors/active", response_model=List[VisitorResponse])
def get_active_visitors(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Get active visitor bookings (not completed)"""
    visitors = db.query(Visitor).filter(
        Visitor.resident_id == current_user.id,
        Visitor.status.in_(["pending", "approved"])
    ).all()
    
    enhanced_visitors = []
    for visitor in visitors:
        visitor_data = VisitorResponse.from_orm(visitor)
        if visitor.slot_id:
            slot = db.query(Slot).filter(Slot.id == visitor.slot_id).first()
            if slot:
                visitor_data.slot_number = slot.slot_number
        enhanced_visitors.append(visitor_data)
    
    return enhanced_visitors

@router2.delete("/visitors/{visitor_id}")
def cancel_visitor_booking(
    visitor_id: int,
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Cancel a visitor booking"""
    visitor = db.query(Visitor).filter(
        Visitor.id == visitor_id,
        Visitor.resident_id == current_user.id
    ).first()
    
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor booking not found")
    
    # Free up the slot if assigned
    if visitor.slot_id:
        slot = db.query(Slot).filter(Slot.id == visitor.slot_id).first()
        if slot:
            slot.status = "available"
    
    db.delete(visitor)
    db.commit()
    
    return {"message": "Visitor booking cancelled successfully"}

@router2.get("/visitors/pending-approval", response_model=List[VisitorResponse])
def get_pending_approval_visitors(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Get unplanned visitors waiting for resident approval"""
    visitors = db.query(Visitor).filter(
        Visitor.resident_id == current_user.id,
        Visitor.status == "pending",  # Unplanned visitors waiting approval
        Visitor.slot_id == None  # No slot assigned yet
    ).all()
    
    enhanced_visitors = []
    for visitor in visitors:
        visitor_data = VisitorResponse.from_orm(visitor)
        enhanced_visitors.append(visitor_data)
    
    return enhanced_visitors

# ========== REQUEST MANAGEMENT ==========
router3 = APIRouter()
@router3.get("/requests", response_model=List[RequestResponse])
def get_my_requests(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Get all requests made by the resident"""
    requests = db.query(Request).filter(Request.resident_id == current_user.id).all()
    
    # Enhance response with slot info
    enhanced_requests = []
    for req in requests:
        request_data = RequestResponse.from_orm(req)
        slot = db.query(Slot).filter(Slot.id == req.slot_id).first()
        if slot:
            request_data.slot_number = slot.slot_number
        enhanced_requests.append(request_data)
    
    return enhanced_requests

@router3.get("/requests/pending", response_model=List[RequestResponse])
def get_pending_requests(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Get pending requests"""
    requests = db.query(Request).filter(
        Request.resident_id == current_user.id,
        Request.status == "pending"
    ).all()
    
    enhanced_requests = []
    for req in requests:
        request_data = RequestResponse.from_orm(req)
        slot = db.query(Slot).filter(Slot.id == req.slot_id).first()
        if slot:
            request_data.slot_number = slot.slot_number
        enhanced_requests.append(request_data)
    
    return enhanced_requests

# ========== NOTIFICATION MANAGEMENT ==========
router4 = APIRouter()
@router4.get("/notifications", response_model=List[Notification])
def get_my_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Get resident's notifications"""
    return notification_crud.get_user_notifications(db, current_user.id, unread_only)

@router4.put("/notifications/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    return notification_crud.mark_notification_as_read(db, notification_id, current_user.id)

@router4.put("/notifications/read-all")
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    return notification_crud.mark_all_notifications_as_read(db, current_user.id)

@router4.get("/notifications/unread-count")
def get_unread_notifications_count(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications"""
    notifications = notification_crud.get_user_notifications(db, current_user.id, unread_only=True)
    return {"unread_count": len(notifications)}

# ========== DASHBOARD ==========
router5 = APIRouter()
@router5.get("/dashboard")
def get_resident_dashboard(
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Get resident dashboard summary"""
    # Get assigned slot
    assigned_slot = None
    if current_user.assigned_slot_id:
        slot = db.query(Slot).filter(Slot.id == current_user.assigned_slot_id).first()
        if slot:
            assigned_slot = {
                "id": slot.id,
                "slot_number": slot.slot_number,
                "slot_type": slot.slot_type,
                "status": slot.status
            }
    
    # Get active visitors
    active_visitors = db.query(Visitor).filter(
        Visitor.resident_id == current_user.id,
        Visitor.status.in_(["approved"])
    ).all()
    
    # Get pending approval visitors (unplanned visitors)
    pending_approval_visitors = db.query(Visitor).filter(
        Visitor.resident_id == current_user.id,
        Visitor.status == "pending",
        Visitor.slot_id == None
    ).all()
    
    # Get pending requests
    pending_requests = db.query(Request).filter(
        Request.resident_id == current_user.id,
        Request.status == "pending"
    ).all()
    
    # Get unread notifications count
    from app.crud.notification_crud import get_user_notifications
    unread_notifications = get_user_notifications(db, current_user.id, unread_only=True)
    
    return {
        "assigned_slot": assigned_slot,
        "active_visitors": [
            {
                "id": visitor.id,
                "visitor_name": visitor.visitor_name,
                "vehicle_number": visitor.vehicle_number,
                "status": visitor.status,
                "entry_time": visitor.entry_time
            } for visitor in active_visitors
        ],
        "pending_approval_visitors": [  # NEW: Show unplanned visitors waiting approval
            {
                "id": visitor.id,
                "visitor_name": visitor.visitor_name,
                "vehicle_number": visitor.vehicle_number,
                "entry_time": visitor.entry_time
            } for visitor in pending_approval_visitors
        ],
        "pending_requests": [
            {
                "id": req.id,
                "request_type": req.request_type,
                "status": req.status,
                "created_at": req.created_at if hasattr(req, 'created_at') else None
            } for req in pending_requests
        ],
        "notifications_count": len(unread_notifications)
    }
# ========== WEB SOCKET FOR REAL-TIME COMMUNICATION ==========

@router5.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time notifications"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages if any
            data = await websocket.receive_text()
            # You can handle incoming messages from client here if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# ========== VISITOR APPROVAL (FOR UNPLANNED VISITORS) ==========
router6 = APIRouter()
@router6.post("/visitors/{visitor_id}/approve")
def approve_unplanned_visitor(
    visitor_id: int,
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Approve an unplanned visitor (sent by admin for approval)"""
    visitor = db.query(Visitor).filter(
        Visitor.id == visitor_id,
        Visitor.resident_id == current_user.id,
        Visitor.status == "pending"
    ).first()
    
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor request not found")
    
    # Find available slot
    available_slot = db.query(Slot).filter(
        Slot.slot_type == visitor.vehicle_type,
        Slot.status == "available"
    ).first()
    
    if not available_slot:
        raise HTTPException(
            status_code=400,
            detail="No available slots for this vehicle type"
        )
    
    # Assign slot and approve
    visitor.slot_id = available_slot.id
    visitor.status = "approved"
    available_slot.status = "occupied"
    
    db.commit()
    
    return {"message": f"Visitor approved and assigned slot {available_slot.slot_number}"}

@router6.post("/visitors/{visitor_id}/reject")
def reject_unplanned_visitor(
    visitor_id: int,
    current_user: User = Depends(get_current_resident),
    db: Session = Depends(get_db)
):
    """Reject an unplanned visitor"""
    visitor = db.query(Visitor).filter(
        Visitor.id == visitor_id,
        Visitor.resident_id == current_user.id,
        Visitor.status == "pending"
    ).first()
    
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor request not found")
    
    visitor.status = "rejected"
    db.commit()
    
    return {"message": "Visitor request rejected"}