import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlmodel import Session, col, or_, select

from app.database import get_session
from app.models import Event, EventReview, EventUserStatus, User, UserEvent
from app.schemas import (
    MyEventsResponse,
    UserAverageReviewRead,
    UserPublic,
    UserRead,
    UserUpdate,
)
from app.security import get_current_user
from app.services import event_to_read_dict

router = APIRouter(prefix="/users", tags=["users"])

AVATARS_DIR = Path("storage/avatars")
MAX_AVATAR_SIZE = 5 * 1024 * 1024

ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


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


@router.get("/search", response_model=list[UserPublic])
def search_users(
    search_query: Optional[str] = None,
    university: Optional[str] = None,
    faculty: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    statement = select(User)

    if search_query:
        pattern = f"%{search_query}%"
        statement = statement.where(
            or_(
                col(User.first_name).ilike(pattern),
                col(User.last_name).ilike(pattern),
            )
        )

    if university:
        statement = statement.where(User.university == university)

    if faculty:
        statement = statement.where(User.faculty == faculty)

    statement = statement.offset((page - 1) * size).limit(size)

    return session.exec(statement).all()


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


@router.get("/{user_id}/reviews/average", response_model=UserAverageReviewRead)
def get_user_reviews_average(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    statement = (
        select(
            func.avg(EventReview.rating),
            func.count(col(EventReview.id)),
        )
        .select_from(Event)
        .join(EventReview, col(EventReview.event_id) == col(Event.id))
        .where(Event.organizer_id == user_id)
    )

    average_rating, total_reviews_count = session.exec(statement).one()

    return UserAverageReviewRead(
        user_id=user_id,
        average_rating=round(float(average_rating), 2) if average_rating is not None else 0.0,
        total_reviews_count=total_reviews_count,
    )


@router.post("/me/avatar", response_model=UserRead)
def upload_my_avatar(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(status_code=400, detail="Dozwolone są tylko pliki JPG, PNG lub WEBP")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="Maksymalny rozmiar pliku to 5 MB")

    AVATARS_DIR.mkdir(parents=True, exist_ok=True)

    extension = ALLOWED_AVATAR_TYPES[file.content_type]
    filename = f"user_{current_user.id}{extension}"
    file_path = AVATARS_DIR / filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.avatar_url = f"/static/avatars/{filename}"

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user