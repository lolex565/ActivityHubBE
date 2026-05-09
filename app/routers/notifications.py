from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Notification, User
from app.schemas import NotificationRead
from app.security import get_current_user

router = APIRouter(tags=["notifications"])


@router.get("/users/me/notifications", response_model=list[NotificationRead])
def get_my_notifications(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    ).all()


@router.patch("/notifications/{notification_id}/read", response_model=NotificationRead)
def mark_notification_as_read(
    notification_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    notification = session.get(Notification, notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Powiadomienie nie istnieje")

    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Brak dostępu do tego powiadomienia")

    notification.is_read = True
    session.add(notification)
    session.commit()
    session.refresh(notification)

    return notification
