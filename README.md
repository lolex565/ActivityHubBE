# ActivityHub Backend

Prototyp backendu dla ActivityHub.

Stack:

- FastAPI
- SQLModel
- PostgreSQL
- JWT
- Docker Compose

## Uruchomienie lokalne

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

## Testy
```bash
pytest ./tests/test_full_flow.py -v -s
```

API:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

## Uruchomienie przez Docker

```bash
docker compose up --build
```

## Wejście do bazy

```bash
docker exec -it activityhub-db psql -U activityhub -d activityhub_db
```

## Główne endpointy

Auth:

- POST /auth/register
- POST /auth/login

Users:

- GET /users/me
- PATCH /users/me
- GET /users
- GET /users/{id}
- GET /users/me/events
- GET /users/me/notifications

Events:

- POST /events
- GET /events
- GET /events/{id}
- PATCH /events/{id}
- DELETE /events/{id}
- GET /events/map
- POST /events/{id}/join
- DELETE /events/{id}/leave
- GET /events/{id}/participants
- POST /events/{id}/interest

Messages:

- POST /events/{id}/messages
- GET /events/{id}/messages

Announcements:

- POST /events/{id}/announcements
- GET /events/{id}/announcements
- PATCH /announcements/{id}
- DELETE /announcements/{id}

Notifications:

- GET /users/me/notifications
- PATCH /notifications/{id}/read
