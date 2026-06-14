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
            "first_name": "Joined",
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


def create_active_event(headers: dict):
    event_date = (date.today() + timedelta(days=1)).isoformat()

    response = requests.post(
        f"{BASE_URL}/events",
        json={
            "name": "Joined Details Test Event",
            "description": "Event for testing joined flag in details",
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


def test_event_details_returns_joined_true_for_participant():
    unique = uuid.uuid4().hex

    organizer = register_user(f"joined_details_organizer_{unique}@student.pwr.edu.pl")
    participant = register_user(f"joined_details_participant_{unique}@student.pwr.edu.pl")

    organizer_headers = login_user(organizer["email"])
    participant_headers = login_user(participant["email"])

    event = create_active_event(organizer_headers)

    join_response = requests.post(
        f"{BASE_URL}/events/{event['id']}/join",
        headers=participant_headers,
    )

    assert join_response.status_code == 200, join_response.text

    details_response = requests.get(
        f"{BASE_URL}/events/{event['id']}",
        headers=participant_headers,
    )

    assert details_response.status_code == 200, details_response.text
    assert details_response.json()["id"] == event["id"]
    assert details_response.json()["joined"] is True


def test_event_details_returns_joined_false_for_interested_user():
    unique = uuid.uuid4().hex

    organizer = register_user(f"joined_interest_organizer_{unique}@student.pwr.edu.pl")
    interested_user = register_user(f"joined_interest_user_{unique}@student.pwr.edu.pl")

    organizer_headers = login_user(organizer["email"])
    interested_headers = login_user(interested_user["email"])

    event = create_active_event(organizer_headers)

    interest_response = requests.post(
        f"{BASE_URL}/events/{event['id']}/interest",
        headers=interested_headers,
    )

    assert interest_response.status_code == 200, interest_response.text

    details_response = requests.get(
        f"{BASE_URL}/events/{event['id']}",
        headers=interested_headers,
    )

    assert details_response.status_code == 200, details_response.text
    assert details_response.json()["id"] == event["id"]
    assert details_response.json()["joined"] is False