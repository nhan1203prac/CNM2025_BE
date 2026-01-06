from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.notification import Notification
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationResponse

router = APIRouter()

@router.get("/", response_model=List[NotificationResponse])
def get_my_notifications(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()

@router.post("/mark-all-read")
def mark_all_as_read(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id, 
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "Đã đánh dấu tất cả là đã đọc"}

@router.put("/{notification_id}/read")
def mark_one_as_read(
    notification_id: int,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id, 
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")
    
    notif.is_read = True
    db.commit()
    return {"message": "Đã đọc"}