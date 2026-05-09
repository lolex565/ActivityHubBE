from datetime import date, datetime, time
from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


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


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    password_hash: str
    birth_date: Optional[date] = None
    email_verified: bool = False
    identity_confirmed: bool = False
    role: UserRole = Field(
        default=UserRole.USER,
        sa_column=Column(SAEnum(UserRole, name="user_role"), nullable=False),
    )
    university: Optional[str] = Field(default=None, max_length=255)
    faculty: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserSettings(SQLModel, table=True):
    __tablename__ = "user_settings"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    event_announcements: bool = True
    calendar_reminders: bool = True


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    organizer_id: int = Field(foreign_key="users.id", index=True)

    name: str = Field(max_length=255)
    description: Optional[str] = None
    type: Optional[str] = Field(default=None, max_length=100, index=True)
    location_name: Optional[str] = Field(default=None, max_length=255, index=True)

    latitude: float
    longitude: float

    event_date: date = Field(index=True)
    event_time: time
    max_participants: Optional[int] = None

    status: EventStatus = Field(
        default=EventStatus.ACTIVE,
        sa_column=Column(SAEnum(EventStatus, name="event_status"), nullable=False, index=True),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserEvent(SQLModel, table=True):
    __tablename__ = "user_events"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    event_id: int = Field(foreign_key="events.id", primary_key=True)
    status: EventUserStatus = Field(
        sa_column=Column(SAEnum(EventUserStatus, name="event_user_status"), nullable=False),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Rating(SQLModel, table=True):
    __tablename__ = "ratings"

    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="users.id")
    event_id: Optional[int] = Field(default=None, foreign_key="events.id")
    rated_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    score: int
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Announcement(SQLModel, table=True):
    __tablename__ = "announcements"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    announcement_date: date
    announcement_time: time
    name: str = Field(max_length=255)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    content: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
