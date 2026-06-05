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
            "last_name": "Owner",
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


def create_post(headers: dict, content: str):
    response = requests.post(
        f"{BASE_URL}/users/me/posts",
        json={"content": content},
        headers=headers,
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_author_can_update_and_delete_own_profile_post():
    unique = uuid.uuid4().hex

    user = register_user(f"profile_post_owner_{unique}@student.pwr.edu.pl")
    headers = login_user(user["email"])

    post = create_post(headers, "Stara treść posta")

    update_response = requests.patch(
        f"{BASE_URL}/users/profile-posts/{post['id']}",
        json={"content": "Nowa treść posta"},
        headers=headers,
    )

    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["id"] == post["id"]
    assert update_response.json()["content"] == "Nowa treść posta"

    delete_response = requests.delete(
        f"{BASE_URL}/users/profile-posts/{post['id']}",
        headers=headers,
    )

    assert delete_response.status_code == 204, delete_response.text

    posts_response = requests.get(
        f"{BASE_URL}/users/{user['id']}/posts",
        headers=headers,
    )

    assert posts_response.status_code == 200, posts_response.text

    post_ids = [item["id"] for item in posts_response.json()]

    assert post["id"] not in post_ids


def test_other_user_cannot_update_or_delete_profile_post():
    unique = uuid.uuid4().hex

    owner = register_user(f"profile_post_real_owner_{unique}@student.pwr.edu.pl")
    stranger = register_user(f"profile_post_stranger_{unique}@student.pwr.edu.pl")

    owner_headers = login_user(owner["email"])
    stranger_headers = login_user(stranger["email"])

    post = create_post(owner_headers, "Mój prywatny post")

    update_response = requests.patch(
        f"{BASE_URL}/users/profile-posts/{post['id']}",
        json={"content": "Próba edycji przez obcego"},
        headers=stranger_headers,
    )

    assert update_response.status_code == 403, update_response.text
    assert update_response.json()["detail"] == "Nie możesz edytować cudzego posta"

    delete_response = requests.delete(
        f"{BASE_URL}/users/profile-posts/{post['id']}",
        headers=stranger_headers,
    )

    assert delete_response.status_code == 403, delete_response.text
    assert delete_response.json()["detail"] == "Nie możesz usunąć cudzego posta"


def test_profile_post_update_validates_content_length():
    unique = uuid.uuid4().hex

    user = register_user(f"profile_post_update_limit_{unique}@student.pwr.edu.pl")
    headers = login_user(user["email"])

    post = create_post(headers, "Poprawny post")

    response = requests.patch(
        f"{BASE_URL}/users/profile-posts/{post['id']}",
        json={"content": "A" * 501},
        headers=headers,
    )

    assert response.status_code == 422