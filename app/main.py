from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import create_db_and_tables, engine
from app.routers import announcements, auth, events, messages, notifications, users

from pathlib import Path

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="ActivityHub API")

AVATARS_DIR = Path("storage/avatars")
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static/avatars", StaticFiles(directory=AVATARS_DIR), name="avatars")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/health")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # zmienic na frontend url na prodzie
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(messages.router)
app.include_router(notifications.router)
app.include_router(announcements.router)
