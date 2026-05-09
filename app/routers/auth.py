from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import User, UserSettings
from app.schemas import TokenResponse, UserCreate, UserLogin, UserRead
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.email == payload.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Użytkownik z takim emailem już istnieje")

    user = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        birth_date=payload.birth_date,
        university=payload.university,
        faculty=payload.faculty,
        password_hash=hash_password(payload.password),
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    settings = UserSettings(user_id=user.id)
    session.add(settings)
    session.commit()

    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Niepoprawny email lub hasło")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)
