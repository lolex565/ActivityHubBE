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
            "first_name": "Post",
            "last_name": "Author",
            "birth_date": "2002-08-23",
            "university": "PWR",
            "faculty": "WIT",
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_profile_post_can_be_created():
    unique = uuid.uuid4().hex

    user = register_user(
        f"profile_post_author_{unique}@student.pwr.edu.pl"
    )

    with psycopg2.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO profile_posts (author_id, content)
                VALUES (%s, %s)
                RETURNING id
                """,
                (
                    user["id"],
                    "Hello ActivityHub!",
                ),
            )

            row = cursor.fetchone()

            assert row is not None

            post_id = row[0]

    assert post_id is not None


def test_profile_post_content_limit():
    unique = uuid.uuid4().hex

    user = register_user(
        f"profile_post_limit_{unique}@student.pwr.edu.pl"
    )

    too_long_content = "A" * 501

    with pytest.raises(psycopg2.Error):
        with psycopg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO profile_posts (author_id, content)
                    VALUES (%s, %s)
                    """,
                    (
                        user["id"],
                        too_long_content,
                    ),
                )