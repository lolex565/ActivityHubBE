import time
import requests


BASE_URL = "http://localhost:8000"


def register_user(email: str):
    payload = {
        "email": email,
        "password": "zaq1@WSX",
        "first_name": "Test",
        "last_name": "User",
        "birth_date": "2002-08-23",
        "university": "PWR",
        "faculty": "W4"
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=payload)

    assert response.status_code == 201
    assert response.json()["email"] == email
    assert "password_hash" not in response.json()

    return response.json()


def login_user(email: str):
    payload = {
        "email": email,
        "password": "zaq1@WSX"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=payload)

    assert response.status_code == 200
    assert "access_token" in response.json()

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_full_backend_flow():
    unique = int(time.time())

    organizer_email = f"organizer_{unique}@student.pwr.edu.pl"
    participant_email = f"participant_{unique}@student.pwr.edu.pl"

    # 1. Healthcheck
    health_response = requests.get(f"{BASE_URL}/health")

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"

    # 2. Register organizer
    organizer = register_user(organizer_email)

    assert organizer["first_name"] == "Test"
    assert organizer["last_name"] == "User"
    assert organizer["university"] == "PWR"
    assert organizer["faculty"] == "W4"

    # 3. Login organizer
    organizer_headers = login_user(organizer_email)

    # 4. Get current organizer
    me_response = requests.get(
        f"{BASE_URL}/users/me",
        headers=organizer_headers
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == organizer_email

    # 5. Update organizer profile
    update_payload = {
        "first_name": "Michal",
        "last_name": "Organizer",
        "university": "Politechnika Wrocławska",
        "faculty": "WIT"
    }

    update_response = requests.patch(
        f"{BASE_URL}/users/me",
        json=update_payload,
        headers=organizer_headers
    )

    assert update_response.status_code == 200
    assert update_response.json()["first_name"] == "Michal"
    assert update_response.json()["last_name"] == "Organizer"

    # 6. Create event
    event_payload = {
        "name": "Flanki na Wyspie",
        "description": "Testowe wydarzenie integracyjne",
        "type": "social",
        "location_name": "Wyspa Słodowa",
        "latitude": 51.115,
        "longitude": 17.038,
        "event_date": "2026-06-01",
        "event_time": "18:00:00",
        "max_participants": 10,
        "status": "ACTIVE"
    }

    create_event_response = requests.post(
        f"{BASE_URL}/events",
        json=event_payload,
        headers=organizer_headers
    )

    assert create_event_response.status_code == 201

    event = create_event_response.json()
    event_id = event["id"]

    assert event["name"] == "Flanki na Wyspie"
    assert event["participants_count"] == 0
    # 6.1 Update event
    update_event_payload = {
        "name": "Flanki na Wyspie Updated",
        "description": "Zmieniony opis wydarzenia",
        "type": "social",
        "location_name": "Wyspa Słodowa",
        "latitude": 51.115,
        "longitude": 17.038,
        "event_date": "2026-06-01",
        "event_time": "19:00:00",
        "max_participants": 12,
        "status": "ACTIVE"
    }

    update_event_response = requests.patch(
        f"{BASE_URL}/events/{event_id}",
        json=update_event_payload,
        headers=organizer_headers
    )

    assert update_event_response.status_code == 200, update_event_response.text

    updated_event = update_event_response.json()

    assert updated_event["id"] == event_id
    assert updated_event["name"] == "Flanki na Wyspie Updated"
    assert updated_event["description"] == "Zmieniony opis wydarzenia"
    assert updated_event["event_time"] == "19:00:00"
    assert updated_event["max_participants"] == 12
    assert "participants_count" in updated_event
    
    # 7. Get events list
    events_response = requests.get(f"{BASE_URL}/events")

    assert events_response.status_code == 200
    assert any(item["id"] == event_id for item in events_response.json())

    # 8. Search events
    search_response = requests.get(
        f"{BASE_URL}/events?search=Flanki&type=social&location=Wyspa"
    )

    assert search_response.status_code == 200
    assert any(item["id"] == event_id for item in search_response.json())

    # 9. Get event details
    details_response = requests.get(f"{BASE_URL}/events/{event_id}")

    assert details_response.status_code == 200
    assert details_response.json()["id"] == event_id
    assert details_response.json()["organizer"]["id"] == organizer["id"]

    # 10. Get map events
    map_response = requests.get(f"{BASE_URL}/events/map")

    assert map_response.status_code == 200
    assert any(item["id"] == event_id for item in map_response.json())

    # 11. Register participant
    participant = register_user(participant_email)

    assert participant["email"] == participant_email

    # 12. Login participant
    participant_headers = login_user(participant_email)

    # 13. Join event
    join_response = requests.post(
        f"{BASE_URL}/events/{event_id}/join",
        headers=participant_headers
    )

    assert join_response.status_code == 200

    # 14. Check participants
    participants_response = requests.get(f"{BASE_URL}/events/{event_id}/participants")

    assert participants_response.status_code == 200
    assert any(item["id"] == participant["id"] for item in participants_response.json())

    # 15. Check my events for participant
    my_events_response = requests.get(
        f"{BASE_URL}/users/me/events",
        headers=participant_headers
    )

    assert my_events_response.status_code == 200
    assert any(item["id"] == event_id for item in my_events_response.json()["joined"])

    # 16. Send message
    message_payload = {
        "content": "Cześć, gdzie dokładnie się spotykamy?"
    }

    message_response = requests.post(
        f"{BASE_URL}/events/{event_id}/messages",
        json=message_payload,
        headers=participant_headers
    )

    assert message_response.status_code == 201
    assert message_response.json()["content"] == message_payload["content"]

    # 17. Get messages
    messages_response = requests.get(f"{BASE_URL}/events/{event_id}/messages")

    assert messages_response.status_code == 200
    assert any(item["content"] == message_payload["content"] for item in messages_response.json())

    # 18. Create announcement as organizer
    announcement_payload = {
        "announcement_date": "2026-06-01",
        "announcement_time": "17:30:00",
        "name": "Miejsce spotkania",
        "description": "Spotykamy się przy moście"
    }

    announcement_response = requests.post(
        f"{BASE_URL}/events/{event_id}/announcements",
        json=announcement_payload,
        headers=organizer_headers
    )

    assert announcement_response.status_code == 201
    assert announcement_response.json()["name"] == "Miejsce spotkania"

    # 19. Get announcements
    announcements_response = requests.get(f"{BASE_URL}/events/{event_id}/announcements")

    assert announcements_response.status_code == 200
    assert any(item["name"] == "Miejsce spotkania" for item in announcements_response.json())

    # 20. Organizer should have notification after participant joined
    notifications_response = requests.get(
        f"{BASE_URL}/users/me/notifications",
        headers=organizer_headers
    )

    assert notifications_response.status_code == 200
    assert len(notifications_response.json()) >= 1

    notification_id = notifications_response.json()[0]["id"]

    # 21. Mark notification as read
    read_response = requests.patch(
        f"{BASE_URL}/notifications/{notification_id}/read",
        headers=organizer_headers
    )

    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True

    # 22. Leave event
    leave_response = requests.delete(
        f"{BASE_URL}/events/{event_id}/leave",
        headers=participant_headers
    )

    assert leave_response.status_code == 200