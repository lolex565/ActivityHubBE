from datetime import date, timedelta
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
            "first_name": "Interest",
            "last_name": "User",
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


def create_event(headers: dict):
    event_date = (date.today() + timedelta(days=1)).isoformat()

    response = requests.post(
        f"{BASE_URL}/events",
        json={
            "name": "Uninterest Test Event",
            "description": "Event for testing uninterest",
            "type": "social",
            "location_name": "Wyspa Słodowa",
            "latitude": 51.115,
            "longitude": 17.038,
            "event_date": event_date,
            "event_time": "18:00:00",
            "max_participants": 10,
            "status": "ACTIVE",
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_user_can_uninterest_event():
    unique = uuid.uuid4().hex

    organizer = register_user(f"uninterest_organizer_{unique}@student.pwr.edu.pl")
    participant = register_user(f"uninterest_participant_{unique}@student.pwr.edu.pl")

    organizer_headers = login_user(organizer["email"])
    participant_headers = login_user(participant["email"])

    event = create_event(organizer_headers)

    interest_response = requests.post(
        f"{BASE_URL}/events/{event['id']}/interest",
        headers=participant_headers,
    )

    assert interest_response.status_code == 200, interest_response.text

    uninterest_response = requests.delete(
        f"{BASE_URL}/events/{event['id']}/interest",
        headers=participant_headers,
    )

    assert uninterest_response.status_code == 200, uninterest_response.text
    assert uninterest_response.json()["message"] == "Usunięto zainteresowanie wydarzeniem"


def test_user_cannot_uninterest_event_when_not_interested():
    unique = uuid.uuid4().hex

    organizer = register_user(f"uninterest_missing_organizer_{unique}@student.pwr.edu.pl")
    participant = register_user(f"uninterest_missing_participant_{unique}@student.pwr.edu.pl")

    organizer_headers = login_user(organizer["email"])
    participant_headers = login_user(participant["email"])

    event = create_event(organizer_headers)

    response = requests.delete(
        f"{BASE_URL}/events/{event['id']}/interest",
        headers=participant_headers,
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Użytkownik nie jest zainteresowany wydarzeniem"