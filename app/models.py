from datetime import date, datetime, time, timezone
from enum import Enum
from typing import ClassVar

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel
from sqlalchemy import CheckConstraint, Column, Text, UniqueConstraint, ForeignKey

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    ORGANIZER = "ORGANIZER"


class EventStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    FINISHED = "FINISHED"


class EventUserStatus(str, Enum):
    INTERESTED = "INTERESTED"
    PARTICIPANT = "PARTICIPANT"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__: ClassVar[str] = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    password_hash: str
    birth_date: date | None = None
    email_verified: bool = False
    identity_confirmed: bool = False
    role: UserRole = Field(
        default=UserRole.USER,
        sa_column=Column(SAEnum(UserRole, name="user_role"), nullable=False),
    )
    university: str | None = Field(default=None, max_length=255)
    faculty: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=utc_now)


class UserSettings(SQLModel, table=True):
    __tablename__: ClassVar[str] = "user_settings"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    event_announcements: bool = True
    calendar_reminders: bool = True


class Event(SQLModel, table=True):
    __tablename__: ClassVar[str] = "events"

    id: int | None = Field(default=None, primary_key=True)
    organizer_id: int = Field(foreign_key="users.id", index=True)

    name: str = Field(max_length=255)
    description: str | None = None
    type: str | None = Field(default=None, max_length=100, index=True)
    location_name: str | None = Field(default=None, max_length=255, index=True)

    latitude: float
    longitude: float

    event_date: date = Field(index=True)
    event_time: time
    max_participants: int | None = None

    status: EventStatus = Field(
        default=EventStatus.ACTIVE,
        sa_column=Column(SAEnum(EventStatus, name="event_status"), nullable=False, index=True),
    )
    created_at: datetime = Field(default_factory=utc_now)


class UserEvent(SQLModel, table=True):
    __tablename__: ClassVar[str] = "user_events"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    event_id: int = Field(foreign_key="events.id", primary_key=True)
    status: EventUserStatus = Field(
        sa_column=Column(SAEnum(EventUserStatus, name="event_user_status"), nullable=False),
    )
    created_at: datetime = Field(default_factory=utc_now)


class EventReview(SQLModel, table=True):
    __tablename__: ClassVar[str] = "event_reviews"
    __table_args__ = (
        UniqueConstraint("event_id", "author_id", name="uq_event_reviews_event_author"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_event_reviews_rating_range"),
        CheckConstraint("char_length(comment) <= 1000", name="ck_event_reviews_comment_length"),
    )

    id: int | None = Field(default=None, primary_key=True)

    event_id: int = Field(
        sa_column=Column(
            ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    author_id: int = Field(
        sa_column=Column(
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    rating: int
    comment: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=utc_now)
    
class Announcement(SQLModel, table=True):
    __tablename__: ClassVar[str] = "announcements"

    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    announcement_date: date
    announcement_time: time
    name: str = Field(max_length=255)
    description: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Message(SQLModel, table=True):
    __tablename__: ClassVar[str] = "messages"

    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class Notification(SQLModel, table=True):
    __tablename__: ClassVar[str] = "notifications"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    event_id: int | None = Field(default=None, foreign_key="events.id", index=True)
    title: str = Field(max_length=255)
    content: str | None = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=utc_now)