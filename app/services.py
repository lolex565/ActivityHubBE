from sqlmodel import Session, select
from typing import Optional

from app.models import Event, EventUserStatus, UserEvent, User


def count_event_participants(session: Session, event_id: int) -> int:
    statement = select(UserEvent).where(
        UserEvent.event_id == event_id,
        UserEvent.status == EventUserStatus.PARTICIPANT,
    )
    return len(session.exec(statement).all())

def check_event_participation(session: Session, event_id: int, curr_user: Optional[User]) -> bool:
    if curr_user:
        statement = select(UserEvent).where(
            UserEvent.event_id == event_id,
            UserEvent.user_id == curr_user.id
        )
        return bool(len(session.exec(statement).all()))
    return False


def event_to_read_dict(session: Session, event: Event, curr_user: Optional[User] = None) -> dict:
    session.refresh(event)

    return {
        "id": event.id,
        "organizer_id": event.organizer_id,
        "name": event.name,
        "description": event.description,
        "type": event.type,
        "location_name": event.location_name,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "event_date": event.event_date,
        "event_time": event.event_time,
        "max_participants": event.max_participants,
        "status": event.status,
        "created_at": event.created_at,
        "participants_count": count_event_participants(session, event.id),
        "joined": check_event_participation(session, event.id, curr_user),
    }
