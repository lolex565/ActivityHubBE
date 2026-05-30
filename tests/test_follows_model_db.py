import uuid

import psycopg2
import pytest
import requests


BASE_URL = "http://localhost:8000"
PASSWORD = "zaq1@WSX"
DATABASE_URL = "postgresql://activityhub:activityhub123@localhost:5432/activityhub_db"


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
            "faculty": "W4",
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_follows_table_allows_follow_between_two_users():
    unique = uuid.uuid4().hex

    follower = register_user(f"follower_{unique}@student.pwr.edu.pl")
    followed = register_user(f"followed_{unique}@student.pwr.edu.pl")

    with psycopg2.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO follows (follower_id, followed_id)
                VALUES (%s, %s)
                """,
                (follower["id"], followed["id"]),
            )

            cursor.execute(
                """
                SELECT follower_id, followed_id
                FROM follows
                WHERE follower_id = %s AND followed_id = %s
                """,
                (follower["id"], followed["id"]),
            )

            result = cursor.fetchone()

    assert result == (follower["id"], followed["id"])


def test_follows_table_blocks_self_follow():
    unique = uuid.uuid4().hex
    user = register_user(f"self_follow_{unique}@student.pwr.edu.pl")

    with pytest.raises(psycopg2.Error):
        with psycopg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO follows (follower_id, followed_id)
                    VALUES (%s, %s)
                    """,
                    (user["id"], user["id"]),
                )