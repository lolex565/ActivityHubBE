from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Event, EventUserStatus, User, UserEvent
from app.schemas import MyEventsResponse, UserRead, UserUpdate
from app.security import get_current_user
from app.services import event_to_read_dict

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(current_user, key, value)

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user


@router.get("", response_model=list[UserRead])
def get_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()


@router.get("/me/events", response_model=MyEventsResponse)
def get_my_events(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    organized_events = session.exec(
        select(Event).where(Event.organizer_id == current_user.id)
    ).all()

    joined_links = session.exec(
        select(UserEvent).where(
            UserEvent.user_id == current_user.id,
            UserEvent.status == EventUserStatus.PARTICIPANT,
        )
    ).all()

    joined_events = []
    for link in joined_links:
        event = session.get(Event, link.event_id)
        if event:
            joined_events.append(event)

    return {
        "organized": [event_to_read_dict(session, event) for event in organized_events],
        "joined": [event_to_read_dict(session, event) for event in joined_events],
    }


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    return user
