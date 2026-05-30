from datetime import date, timedelta
import time

import requests


BASE_URL = "http://localhost:8000"
PASSWORD = "zaq1@WSX"


def register_user(email: str):
    payload = {
        "email": email,
        "password": PASSWORD,
        "first_name": "Test",
        "last_name": "User",
        "birth_date": "2002-08-23",
        "university": "PWR",
        "faculty": "W4",
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
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
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_review_notification_is_created_when_event_is_finished():
    unique = int(time.time())
    past_date = (date.today() - timedelta(days=1)).isoformat()

    organizer = register_user(f"organizer_review_notification_{unique}@student.pwr.edu.pl")
    participant = register_user(f"participant_review_notification_{unique}@student.pwr.edu.pl")

    organizer_headers = login_user(organizer["email"])
    participant_headers = login_user(participant["email"])

    event_payload = {
        "name": "Review Notification Test Event",
        "description": "Event used for testing review notification",
        "type": "social",
        "location_name": "Wyspa Słodowa",
        "latitude": 51.115,
        "longitude": 17.038,
        "event_date": past_date,
        "event_time": "18:00:00",
        "max_participants": 10,
        "status": "ACTIVE",
    }

    create_event_response = requests.post(
        f"{BASE_URL}/events",
        json=event_payload,
        headers=organizer_headers,
    )

    assert create_event_response.status_code == 201, create_event_response.text
    event = create_event_response.json()

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

    notifications_response = requests.get(
        f"{BASE_URL}/users/me/notifications",
        headers=participant_headers,
    )

    assert notifications_response.status_code == 200, notifications_response.text

    notifications = notifications_response.json()

    review_notifications = [
        notification
        for notification in notifications
        if notification["event_id"] == event["id"]
        and notification["title"] == "Wydarzenie zakończone"
    ]

    assert len(review_notifications) == 1

    notification = review_notifications[0]

    assert notification["is_read"] is False
    assert (
        notification["content"]
        == "Wydarzenie Review Notification Test Event zostało zakończone przez organizatora! "
        "Podziel się swoją opinią i wystaw recenzję."
    )