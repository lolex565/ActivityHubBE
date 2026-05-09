from sqlmodel import Session, select

from app.models import Event, EventUserStatus, UserEvent


def count_event_participants(session: Session, event_id: int) -> int:
    statement = select(UserEvent).where(
        UserEvent.event_id == event_id,
        UserEvent.status == EventUserStatus.PARTICIPANT,
    )
    return len(session.exec(statement).all())


def event_to_read_dict(session: Session, event: Event) -> dict:
    data = event.model_dump()
    data["participants_count"] = count_event_participants(session, event.id)
    return data
