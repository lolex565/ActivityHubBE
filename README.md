# ActivityHub Backend

Backend aplikacji ActivityHub zbudowany w oparciu o FastAPI, PostgreSQL oraz Docker.

## Wymagania

Przed uruchomieniem projektu upewnij się, że masz zainstalowane:

* Docker
* Docker Compose
* Git

Opcjonalnie (do uruchamiania testów lokalnie):

* Python 3.12+
* pip
* virtualenv

---

# Klonowanie repozytorium

```bash
git clone <REPOSITORY_URL>
cd activityhub_backend
```

---

# Uruchomienie projektu

## 1. Zbudowanie i uruchomienie kontenerów

```bash
docker compose up --build -d
```

Sprawdzenie statusu:

```bash
docker compose ps
```

Powinny zostać uruchomione:

* postgres
* backend
* pgweb_activityhub

---

## 2. Dostęp do aplikacji

### Backend API

```text
http://localhost:8000
```

### Swagger UI

```text
http://localhost:8000/docs
```


---

# Dane bazy danych

Domyślna konfiguracja PostgreSQL:

```text
Host: localhost
Port: 5432
Database: activityhub_db
User: activityhub
Password: activityhub123
```

---

# Migracje

Migracje znajdują się w katalogu:

```text
migrations/
```

Uruchomienie pojedynczej migracji:

```bash
docker compose exec -T postgres \
psql -U activityhub -d activityhub_db \
< migrations/<migration_file>.sql
```

Przykład:

```bash
docker compose exec -T postgres \
psql -U activityhub -d activityhub_db \
< migrations/001_create_event_reviews.sql
```

---

# Uruchamianie testów

## Przygotowanie środowiska

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instalacja zależności:

```bash
pip install -r requirements.txt
```

---

## Uruchomienie wszystkich testów

```bash
pytest
```

---

## Uruchomienie pojedynczego testu

```bash
pytest tests/test_full_flow.py
```

lub

```bash
pytest tests/test_review_notifications.py
```

---

# Struktura projektu

```text
activityhub_backend
│
├── app
│   ├── routers
│   │   ├── announcements.py
│   │   ├── auth.py
│   │   ├── events.py
│   │   ├── messages.py
│   │   ├── notifications.py
│   │   └── users.py
│   │
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── services.py
│
├── migrations
├── tests
├── storage
│   └── avatars
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# Logowanie do API

1. Utwórz konto:

```http
POST /auth/register
```

2. Zaloguj się:

```http
POST /auth/login
```

3. Skopiuj `access_token`.

4. W Swaggerze kliknij:

```text
Authorize
```

i wklej:

```text
Bearer <access_token>
```

---

# Najczęstsze problemy

## Backend nie odpowiada

Sprawdź logi:

```bash
docker compose logs backend
```

---

## Baza danych nie działa

Sprawdź logi PostgreSQL:

```bash
docker compose logs postgres
```

---

## Reset lokalnej bazy

Usunięcie wszystkich danych:

```bash
docker compose down -v
docker compose up --build -d
```

Uwaga: usunie wszystkie dane zapisane lokalnie.

---

# Technologie

* FastAPI
* SQLModel
* PostgreSQL
* JWT Authentication
* Docker
* Pytest

