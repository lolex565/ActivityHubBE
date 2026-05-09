from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Announcement, Event, User
from app.schemas import AnnouncementCreate, AnnouncementRead, AnnouncementUpdate
from app.security import get_current_user

router = APIRouter(tags=["announcements"])


def require_event(session: Session, event_id: int) -> Event:
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Wydarzenie nie istnieje")
    return event


def require_organizer(event: Event, user: User) -> None:
    if event.organizer_id != user.id:
        raise HTTPException(status_code=403, detail="Tylko organizator może wykonać tę akcję")


@router.post("/events/{event_id}/announcements", response_model=AnnouncementRead, status_code=status.HTTP_201_CREATED)
def create_announcement(
    event_id: int,
    payload: AnnouncementCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    event = require_event(session, event_id)
    require_organizer(event, current_user)

    announcement = Announcement(event_id=event_id, **payload.model_dump())

    session.add(announcement)
    session.commit()
    session.refresh(announcement)

    return announcement


@router.get("/events/{event_id}/announcements", response_model=list[AnnouncementRead])
def get_event_announcements(event_id: int, session: Session = Depends(get_session)):
    require_event(session, event_id)

    return session.exec(
        select(Announcement)
        .where(Announcement.event_id == event_id)
        .order_by(Announcement.announcement_date, Announcement.announcement_time)
    ).all()


@router.patch("/announcements/{announcement_id}", response_model=AnnouncementRead)
def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    announcement = session.get(Announcement, announcement_id)

    if not announcement:
        raise HTTPException(status_code=404, detail="Ogłoszenie nie istnieje")

    event = require_event(session, announcement.event_id)
    require_organizer(event, current_user)

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(announcement, key, value)

    session.add(announcement)
    session.commit()
    session.refresh(announcement)

    return announcement


@router.delete("/announcements/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    announcement = session.get(Announcement, announcement_id)

    if not announcement:
        raise HTTPException(status_code=404, detail="Ogłoszenie nie istnieje")

    event = require_event(session, announcement.event_id)
    require_organizer(event, current_user)

    session.delete(announcement)
    session.commit()

    return {"message": "Usunięto ogłoszenie"}
