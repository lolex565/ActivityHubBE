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
            "first_name": "Post",
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


def test_user_can_create_and_read_profile_posts_sorted_newest_first():
    unique = uuid.uuid4().hex

    user = register_user(f"profile_posts_{unique}@student.pwr.edu.pl")
    headers = login_user(user["email"])

    first_response = requests.post(
        f"{BASE_URL}/users/me/posts",
        json={"content": "Pierwszy post"},
        headers=headers,
    )

    assert first_response.status_code == 201, first_response.text

    second_response = requests.post(
        f"{BASE_URL}/users/me/posts",
        json={"content": "Drugi post"},
        headers=headers,
    )

    assert second_response.status_code == 201, second_response.text

    posts_response = requests.get(
        f"{BASE_URL}/users/{user['id']}/posts",
        headers=headers,
    )

    assert posts_response.status_code == 200, posts_response.text

    posts = posts_response.json()

    assert len(posts) >= 2
    assert posts[0]["content"] == "Drugi post"
    assert posts[1]["content"] == "Pierwszy post"


def test_profile_post_rejects_too_long_content():
    unique = uuid.uuid4().hex

    user = register_user(f"profile_posts_long_{unique}@student.pwr.edu.pl")
    headers = login_user(user["email"])

    response = requests.post(
        f"{BASE_URL}/users/me/posts",
        json={"content": "A" * 501},
        headers=headers,
    )

    assert response.status_code == 422


def test_profile_post_rejects_empty_content():
    unique = uuid.uuid4().hex

    user = register_user(f"profile_posts_empty_{unique}@student.pwr.edu.pl")
    headers = login_user(user["email"])

    response = requests.post(
        f"{BASE_URL}/users/me/posts",
        json={"content": ""},
        headers=headers,
    )

    assert response.status_code == 422