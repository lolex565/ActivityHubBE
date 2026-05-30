from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import EventStatus, EventUserStatus, UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    university: Optional[str] = None
    faculty: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    email_verified: bool
    identity_confirmed: bool
    role: UserRole
    university: Optional[str] = None
    faculty: Optional[str] = None
    created_at: datetime


class UserPublic(BaseModel):
    id: int
    first_name: str
    last_name: str
    university: Optional[str] = None
    faculty: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    university: Optional[str] = None
    faculty: Optional[str] = None


class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = None
    location_name: Optional[str] = None
    latitude: float
    longitude: float
    event_date: date
    event_time: time
    max_participants: Optional[int] = Field(default=None, gt=0)
    status: EventStatus = EventStatus.ACTIVE


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    event_date: Optional[date] = None
    event_time: Optional[time] = None
    max_participants: Optional[int] = Field(default=None, gt=0)
    status: Optional[EventStatus] = None


class EventRead(BaseModel):
    id: int
    organizer_id: int
    name: str
    description: Optional[str] = None
    type: Optional[str] = None
    location_name: Optional[str] = None
    latitude: float
    longitude: float
    event_date: date
    event_time: time
    max_participants: Optional[int] = None
    status: EventStatus
    created_at: datetime
    participants_count: int = 0
    joined: bool


class EventDetails(EventRead):
    organizer: Optional[UserPublic] = None


class ParticipantRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    university: Optional[str] = None
    faculty: Optional[str] = None
    status: EventUserStatus


class MyEventsResponse(BaseModel):
    organized: list[EventRead]
    joined: list[EventRead]


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class MessageRead(BaseModel):
    id: int
    event_id: int
    user_id: int
    author: Optional[UserPublic] = None
    content: str
    created_at: datetime


class NotificationRead(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    is_read: bool
    created_at: datetime


class AnnouncementCreate(BaseModel):
    announcement_date: date
    announcement_time: time
    name: str
    description: Optional[str] = None


class AnnouncementUpdate(BaseModel):
    announcement_date: Optional[date] = None
    announcement_time: Optional[time] = None
    name: Optional[str] = None
    description: Optional[str] = None


class AnnouncementRead(BaseModel):
    id: int
    event_id: int
    announcement_date: date
    announcement_time: time
    name: str
    description: Optional[str] = None
    created_at: datetime


class MapEventRead(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    status: EventStatus
    event_date: date
    event_time: time
    location_name: Optional[str] = None
    participants_count: int = 0
    max_participants: Optional[int] = None

class EventReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class EventReviewRead(BaseModel):
    id: int
    event_id: int
    author_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime

class UserAverageReviewRead(BaseModel):
    user_id: int
    average_rating: float
    total_reviews_count: int