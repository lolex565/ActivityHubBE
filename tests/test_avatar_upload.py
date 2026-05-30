import io
import time

import requests


BASE_URL = "http://localhost:8000"
PASSWORD = "zaq1@WSX"


def register_user(email: str):
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "first_name": "Avatar",
            "last_name": "User",
            "birth_date": "2002-08-23",
            "university": "PWR",
            "faculty": "W4",
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


def test_user_can_upload_avatar():
    unique = int(time.time())
    user = register_user(f"avatar_user_{unique}@student.pwr.edu.pl")
    headers = login_user(user["email"])

    files = {
        "file": (
            "avatar.png",
            io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 100),
            "image/png",
        )
    }

    response = requests.post(
        f"{BASE_URL}/users/me/avatar",
        files=files,
        headers=headers,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == user["id"]
    assert data["avatar_url"] == f"/static/avatars/user_{user['id']}.png"

    avatar_response = requests.get(f"{BASE_URL}{data['avatar_url']}")

    assert avatar_response.status_code == 200


def test_user_cannot_upload_non_image_avatar():
    unique = int(time.time())
    user = register_user(f"avatar_invalid_{unique}@student.pwr.edu.pl")
    headers = login_user(user["email"])

    files = {
        "file": (
            "document.pdf",
            io.BytesIO(b"%PDF-1.4 fake pdf content"),
            "application/pdf",
        )
    }

    response = requests.post(
        f"{BASE_URL}/users/me/avatar",
        files=files,
        headers=headers,
    )

    assert response.status_code == 400, response.text