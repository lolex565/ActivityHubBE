from datetime import date
from typing import Optional

from requests import session

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, or_, select

from app.database import get_session
from app.models import Event, EventStatus, EventUserStatus, Notification, User, UserEvent
from app.schemas import EventCreate, EventDetails, EventRead, EventUpdate, MapEventRead, ParticipantRead
from app.security import get_current_user
from app.services import count_event_participants, event_to_read_dict

router = APIRouter(prefix="/events", tags=["events"])


def validate_coordinates(latitude: float, longitude: float) -> None:
    if latitude < -90 or latitude > 90:
        raise HTTPException(status_code=400, detail="Latitude musi być od -90 do 90")
    if longitude < -180 or longitude > 180:
        raise HTTPException(status_code=400, detail="Longitude musi być od -180 do 180")


def require_event(session: Session, event_id: int) -> Event:
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Wydarzenie nie istnieje")
    return event


def require_organizer(event: Event, user: User) -> None:
    if event.organizer_id != user.id:
        raise HTTPException(status_code=403, detail="Tylko organizator może wykonać tę akcję")


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    validate_coordinates(payload.latitude, payload.longitude)

    event = Event(
        **payload.model_dump(),
        organizer_id=current_user.id,
    )

    session.add(event)
    session.commit()
    session.refresh(event)

    return event_to_read_dict(session, event)


@router.get("", response_model=list[EventRead])
def get_events(
    search: Optional[str] = None,
    type: Optional[str] = None,
    location: Optional[str] = None,
    status_filter: Optional[EventStatus] = Query(default=None, alias="status"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    session: Session = Depends(get_session),
):
    statement = select(Event)

    if search:
        pattern = f"%{search}%"
        statement = statement.where(
            or_(
                col(Event.name).ilike(pattern),
                col(Event.description).ilike(pattern),
            )
        )

    if type:
        statement = statement.where(Event.type == type)

    if location:
        statement = statement.where(col(Event.location_name).ilike(f"%{location}%"))

    if status_filter:
        statement = statement.where(Event.status == status_filter)

    if date_from:
        statement = statement.where(Event.event_date >= date_from)

    if date_to:
        statement = statement.where(Event.event_date <= date_to)

    statement = statement.order_by(Event.event_date, Event.event_time)

    events = session.exec(statement).all()
    return [event_to_read_dict(session, event) for event in events]


@router.get("/map", response_model=list[MapEventRead])
def get_events_map(session: Session = Depends(get_session)):
    events = session.exec(select(Event).where(Event.status == EventStatus.ACTIVE)).all()

    return [
        {
            **event.model_dump(),
            "participants_count": count_event_participants(session, event.id),
        }
        for event in events
    ]


@router.get("/{event_id}", response_model=EventDetails)
def get_event(event_id: int, session: Session = Depends(get_session)):
    event = require_event(session, event_id)
    organizer = session.get(User, event.organizer_id)

    data = event_to_read_dict(session, event)
    if organizer:
        data["organizer"] = {
            "id": organizer.id,
            "first_name": organizer.first_name,
            "last_name": organizer.last_name,
            "university": organizer.university,
            "faculty": organizer.faculty,
        }

    return data


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    payload: EventUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    event = require_event(session, event_id)
    require_organizer(event, current_user)

    update_data = payload.model_dump(exclude_unset=True)

    latitude = update_data.get("latitude", event.latitude)
    longitude = update_data.get("longitude", event.longitude)
    validate_coordinates(latitude, longitude)

    for key, value in update_data.items():
        setattr(event, key, value)

    session.add(event)
    session.commit()
    session.refresh(event)

    notification_links = session.exec(
        select(UserEvent).where(
            UserEvent.event_id == event.id,
            UserEvent.status == EventUserStatus.PARTICIPANT,
        )
    ).all()

    for link in notification_links:
        if link.user_id != current_user.id:
            session.add(
                Notification(
                    user_id=link.user_id,
                    title="Wydarzenie zostało zmienione",
                    content=f"Organizator zmienił wydarzenie: {event.name}",
                )
            )

    session.commit()
    session.refresh(event)

    return event_to_read_dict(session, event)


@router.delete("/{event_id}")
def cancel_event(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    event = require_event(session, event_id)
    require_organizer(event, current_user)

    event.status = EventStatus.CANCELLED
    session.add(event)

    links = session.exec(
        select(UserEvent).where(
            UserEvent.event_id == event.id,
            UserEvent.status == EventUserStatus.PARTICIPANT,
        )
    ).all()

    for link in links:
        if link.user_id != current_user.id:
            session.add(
                Notification(
                    user_id=link.user_id,
                    title="Wydarzenie zostało anulowane",
                    content=f"Wydarzenie {event.name} zostało anulowane",
                )
            )

    session.commit()

    return {"message": "Wydarzenie zostało anulowane"}


@router.post("/{event_id}/join")
def join_event(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    event = require_event(session, event_id)

    if event.status != EventStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Można dołączać tylko do aktywnych wydarzeń")

    existing = session.get(UserEvent, (current_user.id, event_id))

    if existing and existing.status == EventUserStatus.PARTICIPANT:
        raise HTTPException(status_code=400, detail="Użytkownik już dołączył do wydarzenia")

    participants_count = count_event_participants(session, event_id)
    if event.max_participants is not None and participants_count >= event.max_participants:
        raise HTTPException(status_code=400, detail="Brak wolnych miejsc")

    if existing:
        existing.status = EventUserStatus.PARTICIPANT
        session.add(existing)
    else:
        session.add(
            UserEvent(
                user_id=current_user.id,
                event_id=event_id,
                status=EventUserStatus.PARTICIPANT,
            )
        )

    if event.organizer_id != current_user.id:
        session.add(
            Notification(
                user_id=event.organizer_id,
                title="Nowy uczestnik wydarzenia",
                content=f"{current_user.first_name} {current_user.last_name} dołączył do: {event.name}",
            )
        )

    session.commit()

    return {"message": "Dołączono do wydarzenia"}


@router.delete("/{event_id}/leave")
def leave_event(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    require_event(session, event_id)
    link = session.get(UserEvent, (current_user.id, event_id))

    if not link or link.status != EventUserStatus.PARTICIPANT:
        raise HTTPException(status_code=400, detail="Użytkownik nie jest uczestnikiem wydarzenia")

    session.delete(link)
    session.commit()

    return {"message": "Opuszczono wydarzenie"}


@router.post("/{event_id}/interest")
def interest_event(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    require_event(session, event_id)
    existing = session.get(UserEvent, (current_user.id, event_id))

    if existing:
        existing.status = EventUserStatus.INTERESTED
        session.add(existing)
    else:
        session.add(
            UserEvent(
                user_id=current_user.id,
                event_id=event_id,
                status=EventUserStatus.INTERESTED,
            )
        )

    session.commit()

    return {"message": "Oznaczono zainteresowanie wydarzeniem"}


@router.get("/{event_id}/participants", response_model=list[ParticipantRead])
def get_participants(event_id: int, session: Session = Depends(get_session)):
    require_event(session, event_id)

    links = session.exec(
        select(UserEvent).where(
            UserEvent.event_id == event_id,
            UserEvent.status == EventUserStatus.PARTICIPANT,
        )
    ).all()

    result = []
    for link in links:
        user = session.get(User, link.user_id)
        if user:
            result.append(
                {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "university": user.university,
                    "faculty": user.faculty,
                    "status": link.status,
                }
            )

    return result
