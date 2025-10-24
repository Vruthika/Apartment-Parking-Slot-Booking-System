from sqlalchemy.orm import Session
from app.models.notification import Notification
from fastapi import HTTPException, status

def create_notification(db: Session, user_id: int, title: str, message: str, type: str):
    db_notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_user_notifications(db: Session, user_id: int, unread_only: bool = False):
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).all()

def mark_notification_as_read(db: Session, notification_id: int, user_id: int):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    return notification

def mark_all_notifications_as_read(db: Session, user_id: int):
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).all()
    
    for notification in notifications:
        notification.is_read = True
    
    db.commit()
    return {"message": f"Marked {len(notifications)} notifications as read"}