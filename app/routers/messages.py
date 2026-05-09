from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Event, Message, User
from app.schemas import MessageCreate, MessageRead
from app.security import get_current_user

router = APIRouter(prefix="/events", tags=["messages"])


@router.post("/{event_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def create_message(
    event_id: int,
    payload: MessageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Wydarzenie nie istnieje")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Wiadomość nie może być pusta")

    message = Message(
        event_id=event_id,
        user_id=current_user.id,
        content=content,
    )

    session.add(message)
    session.commit()
    session.refresh(message)

    return {
        **message.model_dump(),
        "author": {
            "id": current_user.id,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "university": current_user.university,
            "faculty": current_user.faculty,
        },
    }


@router.get("/{event_id}/messages", response_model=list[MessageRead])
def get_messages(event_id: int, session: Session = Depends(get_session)):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Wydarzenie nie istnieje")

    messages = session.exec(
        select(Message)
        .where(Message.event_id == event_id)
        .order_by(Message.created_at)
    ).all()

    result = []
    for message in messages:
        user = session.get(User, message.user_id)
        result.append(
            {
                **message.model_dump(),
                "author": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "university": user.university,
                    "faculty": user.faculty,
                } if user else None,
            }
        )

    return result
