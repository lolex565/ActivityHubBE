import uuid

import psycopg2
import requests


BASE_URL = "http://localhost:8000"
PASSWORD = "zaq1@WSX"
DATABASE_URL = "postgresql://activityhub:activityhub123@localhost:5432/activityhub_db"


def register_user(email: str, first_name: str):
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "first_name": first_name,
            "last_name": "FollowTest",
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


def test_user_search_returns_is_followed_indicator():
    unique = uuid.uuid4().hex
    marker = unique[:8]

    logged_user = register_user(
        f"follow_search_logged_{unique}@student.pwr.edu.pl",
        f"Logged{marker}",
    )
    followed_user = register_user(
        f"follow_search_followed_{unique}@student.pwr.edu.pl",
        f"Followed{marker}",
    )
    not_followed_user = register_user(
        f"follow_search_not_followed_{unique}@student.pwr.edu.pl",
        f"NotFollowed{marker}",
    )

    with psycopg2.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO follows (follower_id, followed_id)
                VALUES (%s, %s)
                """,
                (logged_user["id"], followed_user["id"]),
            )

    headers = login_user(logged_user["email"])

    response = requests.get(
        f"{BASE_URL}/users/search",
        params={
            "search_query": marker,
            "faculty": "WIT",
            "university": "PWR",
            "size": 100,
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    users = response.json()
    user_ids = {user["id"] for user in users}

    assert followed_user["id"] in user_ids
    assert not_followed_user["id"] in user_ids

    followed_result = next(user for user in users if user["id"] == followed_user["id"])
    not_followed_result = next(user for user in users if user["id"] == not_followed_user["id"])

    assert followed_result["is_followed"] is True
    assert not_followed_result["is_followed"] is False