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
            "first_name": "Follow",
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


def test_user_can_follow_and_unfollow_another_user():
    unique = uuid.uuid4().hex

    follower = register_user(f"follow_action_follower_{unique}@student.pwr.edu.pl")
    followed = register_user(f"follow_action_followed_{unique}@student.pwr.edu.pl")

    headers = login_user(follower["email"])

    follow_response = requests.post(
        f"{BASE_URL}/users/{followed['id']}/follow",
        headers=headers,
    )

    assert follow_response.status_code == 201, follow_response.text
    assert follow_response.json()["message"] == "Zaobserwowano użytkownika"

    search_response = requests.get(
        f"{BASE_URL}/users/search",
        params={
            "search_query": "Follow",
            "faculty": "WIT",
            "size": 100,
        },
        headers=headers,
    )

    assert search_response.status_code == 200, search_response.text

    followed_result = next(
        user for user in search_response.json()
        if user["id"] == followed["id"]
    )

    assert followed_result["is_followed"] is True

    unfollow_response = requests.delete(
        f"{BASE_URL}/users/{followed['id']}/follow",
        headers=headers,
    )

    assert unfollow_response.status_code == 204, unfollow_response.text

    search_after_unfollow_response = requests.get(
        f"{BASE_URL}/users/search",
        params={
            "search_query": "Follow",
            "faculty": "WIT",
            "size": 100,
        },
        headers=headers,
    )

    assert search_after_unfollow_response.status_code == 200, search_after_unfollow_response.text

    followed_after_unfollow_result = next(
        user for user in search_after_unfollow_response.json()
        if user["id"] == followed["id"]
    )

    assert followed_after_unfollow_result["is_followed"] is False


def test_user_cannot_follow_self():
    unique = uuid.uuid4().hex

    user = register_user(f"follow_self_{unique}@student.pwr.edu.pl")
    headers = login_user(user["email"])

    response = requests.post(
        f"{BASE_URL}/users/{user['id']}/follow",
        headers=headers,
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Nie możesz obserwować samego siebie"


def test_user_cannot_follow_same_user_twice():
    unique = uuid.uuid4().hex

    follower = register_user(f"follow_twice_follower_{unique}@student.pwr.edu.pl")
    followed = register_user(f"follow_twice_followed_{unique}@student.pwr.edu.pl")

    headers = login_user(follower["email"])

    first_response = requests.post(
        f"{BASE_URL}/users/{followed['id']}/follow",
        headers=headers,
    )

    assert first_response.status_code == 201, first_response.text

    second_response = requests.post(
        f"{BASE_URL}/users/{followed['id']}/follow",
        headers=headers,
    )

    assert second_response.status_code == 400, second_response.text
    assert second_response.json()["detail"] == "Już obserwujesz tego użytkownika"


def test_unfollow_non_existing_relation_returns_404():
    unique = uuid.uuid4().hex

    follower = register_user(f"unfollow_missing_follower_{unique}@student.pwr.edu.pl")
    followed = register_user(f"unfollow_missing_followed_{unique}@student.pwr.edu.pl")

    headers = login_user(follower["email"])

    response = requests.delete(
        f"{BASE_URL}/users/{followed['id']}/follow",
        headers=headers,
    )

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Nie obserwujesz tego użytkownika"