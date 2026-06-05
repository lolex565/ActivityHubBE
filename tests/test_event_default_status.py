import uuid

import requests


BASE_URL = "http://localhost:8000"
PASSWORD = "zaq1@WSX"


def register_user(email: str):
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "first_name": "Draft",
            "last_name": "Organizer",
            "birth_date": "2002-08-23",
            "university": "PWR",
            "faculty": "WIT",
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


def login_user(email: str):
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_event_created_without_status_defaults_to_draft():
    unique = uuid.uuid4().hex

    organizer = register_user(f"draft_event_{unique}@student.pwr.edu.pl")
    headers = login_user(organizer["email"])

    payload = {
        "name": "Draft Event Test",
        "description": "Event without explicit status",
        "type": "social",
        "location_name": "Wyspa Słodowa",
        "latitude": 51.115,
        "longitude": 17.038,
        "event_date": "2026-06-01",
        "event_time": "18:00:00",
        "max_participants": 10,
    }

    response = requests.post(
        f"{BASE_URL}/events",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "DRAFT"