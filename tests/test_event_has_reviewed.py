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
            "first_name": "Review",
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


def create_finished_event(organizer_headers: dict):
    past_date = (date.today() - timedelta(days=1)).isoformat()

    create_response = requests.post(
        f"{BASE_URL}/events",
        json={
            "name": "Has Reviewed Test Event",
            "description": "Event for testing has_reviewed flag",
            "type": "social",
            "location_name": "Wyspa Słodowa",
            "latitude": 51.115,
            "longitude": 17.038,
            "event_date": past_date,
            "event_time": "18:00:00",
            "max_participants": 10,
            "status": "ACTIVE",
        },
        headers=organizer_headers,
    )

    assert create_response.status_code == 201, create_response.text
    event = create_response.json()

    finish_response = requests.patch(
        f"{BASE_URL}/events/{event['id']}",
        json={"status": "FINISHED"},
        headers=organizer_headers,
    )

    assert finish_response.status_code == 200, finish_response.text

    return event


def test_event_details_returns_has_reviewed_false_before_review_and_true_after_review():
    unique = uuid.uuid4().hex

    organizer = register_user(f"has_reviewed_organizer_{unique}@student.pwr.edu.pl")
    participant = register_user(f"has_reviewed_participant_{unique}@student.pwr.edu.pl")

    organizer_headers = login_user(organizer["email"])
    participant_headers = login_user(participant["email"])

    event = create_finished_event(organizer_headers)

    join_response = requests.post(
        f"{BASE_URL}/events/{event['id']}/join",
        headers=participant_headers,
    )

    assert join_response.status_code == 400

    activate_response = requests.patch(
        f"{BASE_URL}/events/{event['id']}",
        json={"status": "ACTIVE"},
        headers=organizer_headers,
    )

    assert activate_response.status_code == 200, activate_response.text

    join_response = requests.post(
        f"{BASE_URL}/events/{event['id']}/join",
        headers=participant_headers,
    )

    assert join_response.status_code == 200, join_response.text

    finish_response = requests.patch(
        f"{BASE_URL}/events/{event['id']}",
        json={"status": "FINISHED"},
        headers=organizer_headers,
    )

    assert finish_response.status_code == 200, finish_response.text

    details_before_review_response = requests.get(
        f"{BASE_URL}/events/{event['id']}",
        headers=participant_headers,
    )

    assert details_before_review_response.status_code == 200, details_before_review_response.text
    assert details_before_review_response.json()["joined"] is True
    assert details_before_review_response.json()["has_reviewed"] is False

    review_response = requests.post(
        f"{BASE_URL}/events/{event['id']}/reviews",
        json={
            "rating": 5,
            "comment": "Bardzo dobre wydarzenie",
        },
        headers=participant_headers,
    )

    assert review_response.status_code == 201, review_response.text

    details_after_review_response = requests.get(
        f"{BASE_URL}/events/{event['id']}",
        headers=participant_headers,
    )

    assert details_after_review_response.status_code == 200, details_after_review_response.text
    assert details_after_review_response.json()["joined"] is True
    assert details_after_review_response.json()["has_reviewed"] is True