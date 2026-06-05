import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlmodel import Session, col, or_, select

from app.database import get_session
from app.models import Event, EventReview, EventUserStatus, Follow, User, UserEvent, ProfilePost
from app.schemas import (
    MyEventsResponse,
    UserAverageReviewRead,
    UserPublic,
    UserRead,
    UserUpdate,
    ProfilePostCreate, 
    ProfilePostRead,
    ProfilePostUpdate
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

    users = session.exec(statement).all()
    user_ids = [user.id for user in users if user.id is not None]

    followed_ids = set()

    if user_ids:
        followed_links = session.exec(
            select(Follow.followed_id).where(
                col(Follow.follower_id) == current_user.id,
                col(Follow.followed_id).in_(user_ids),
            )
        ).all()

        followed_ids = set(followed_links)

    return [
        {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "university": user.university,
            "faculty": user.faculty,
            "avatar_url": user.avatar_url,
            "is_followed": user.id in followed_ids,
        }
        for user in users
    ]


@router.get("", response_model=list[UserRead])
def get_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()

@router.get("/{user_id}/following", response_model=list[UserPublic])
def get_user_following(
    user_id: int,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    statement = (
        select(User)
        .join(Follow, col(Follow.followed_id) == col(User.id))
        .where(col(Follow.follower_id) == user_id)
        .offset((page - 1) * size)
        .limit(size)
    )

    users = session.exec(statement).all()

    return [
        {
            "id": followed_user.id,
            "first_name": followed_user.first_name,
            "last_name": followed_user.last_name,
            "university": followed_user.university,
            "faculty": followed_user.faculty,
            "avatar_url": followed_user.avatar_url,
        }
        for followed_user in users
    ]
@router.get("/{user_id}/followers", response_model=list[UserPublic])
def get_user_followers(
    user_id: int,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    statement = (
        select(User)
        .join(Follow, col(Follow.follower_id) == col(User.id))
        .where(col(Follow.followed_id) == user_id)
        .offset((page - 1) * size)
        .limit(size)
    )

    users = session.exec(statement).all()

    return [
        {
            "id": follower_user.id,
            "first_name": follower_user.first_name,
            "last_name": follower_user.last_name,
            "university": follower_user.university,
            "faculty": follower_user.faculty,
            "avatar_url": follower_user.avatar_url,
        }
        for follower_user in users
    ]

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

@router.post("/{user_id}/follow", status_code=201)
def follow_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Niepoprawny token użytkownika")

    current_user_id = current_user.id

    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Nie możesz obserwować samego siebie")

    followed_user = session.get(User, user_id)
    if not followed_user:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    existing_follow = session.get(Follow, (current_user_id, user_id))
    if existing_follow:
        raise HTTPException(status_code=400, detail="Już obserwujesz tego użytkownika")

    follow = Follow(
        follower_id=current_user_id,
        followed_id=user_id,
    )

    session.add(follow)
    session.commit()

    return {"message": "Zaobserwowano użytkownika"}

@router.delete("/{user_id}/follow", status_code=204)
def unfollow_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Niepoprawny token użytkownika")

    current_user_id = current_user.id

    follow = session.get(Follow, (current_user_id, user_id))

    if not follow:
        raise HTTPException(status_code=404, detail="Nie obserwujesz tego użytkownika")

    session.delete(follow)
    session.commit()

    return None

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

@router.post("/me/posts", response_model=ProfilePostRead, status_code=201)
def create_my_profile_post(
    payload: ProfilePostCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Niepoprawny token użytkownika")

    post = ProfilePost(
        author_id=current_user.id,
        content=payload.content,
    )

    session.add(post)
    session.commit()
    session.refresh(post)

    return post

@router.get("/{user_id}/posts", response_model=list[ProfilePostRead])
def get_user_profile_posts(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    statement = (
        select(ProfilePost)
        .where(col(ProfilePost.author_id) == user_id)
        .order_by(col(ProfilePost.created_at).desc())
    )

    return session.exec(statement).all()

@router.patch("/profile-posts/{post_id}", response_model=ProfilePostRead)
def update_profile_post(
    post_id: int,
    payload: ProfilePostUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Niepoprawny token użytkownika")

    post = session.get(ProfilePost, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post nie istnieje")

    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Nie możesz edytować cudzego posta")

    post.content = payload.content

    session.add(post)
    session.commit()
    session.refresh(post)

    return post

@router.delete("/profile-posts/{post_id}", status_code=204)
def delete_profile_post(
    post_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Niepoprawny token użytkownika")

    post = session.get(ProfilePost, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post nie istnieje")

    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Nie możesz usunąć cudzego posta")

    session.delete(post)
    session.commit()

    return None