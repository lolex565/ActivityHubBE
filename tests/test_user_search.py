import uuid

import requests


BASE_URL = "http://localhost:8000"
PASSWORD = "zaq1@WSX"


def register_user(
    email: str,
    first_name: str,
    last_name: str,
    university: str,
    faculty: str,
):
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "first_name": first_name,
            "last_name": last_name,
            "birth_date": "2002-08-23",
            "university": university,
            "faculty": faculty,
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


def test_user_search_filters_by_name_university_and_faculty():
    unique = uuid.uuid4().hex

    logged_user = register_user(
        email=f"search_logged_{unique}@student.pwr.edu.pl",
        first_name="Logged",
        last_name="User",
        university="PWR",
        faculty="W4",
    )

    target_user = register_user(
        email=f"search_target_{unique}@student.pwr.edu.pl",
        first_name="Alicja",
        last_name="Kowalska",
        university="PWR",
        faculty="WIT",
    )

    other_user = register_user(
        email=f"search_other_{unique}@student.pwr.edu.pl",
        first_name="Alicja",
        last_name="Nowak",
        university="UWR",
        faculty="WIT",
    )

    headers = login_user(logged_user["email"])

    response = requests.get(
        f"{BASE_URL}/users/search",
        params={
            "search_query": "alicja",
            "university": "PWR",
            "faculty": "WIT",
            "page": 1,
            "size": 20,
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    data = response.json()
    ids = [user["id"] for user in data]

    assert target_user["id"] in ids
    assert other_user["id"] not in ids

    matched_user = next(user for user in data if user["id"] == target_user["id"])

    assert matched_user["first_name"] == "Alicja"
    assert matched_user["last_name"] == "Kowalska"
    assert matched_user["university"] == "PWR"
    assert matched_user["faculty"] == "WIT"
    assert "avatar_url" in matched_user


def test_user_search_is_case_insensitive_for_last_name():
    unique = uuid.uuid4().hex

    logged_user = register_user(
        email=f"search_logged_case_{unique}@student.pwr.edu.pl",
        first_name="Logged",
        last_name="User",
        university="PWR",
        faculty="W4",
    )

    target_user = register_user(
        email=f"search_case_target_{unique}@student.pwr.edu.pl",
        first_name="Jan",
        last_name="Wiśniewski",
        university="PWR",
        faculty="WIT",
    )

    headers = login_user(logged_user["email"])

    response = requests.get(
        f"{BASE_URL}/users/search",
        params={
            "search_query": "wiśn",
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    ids = [user["id"] for user in response.json()]

    assert target_user["id"] in ids


def test_user_search_requires_authentication():
    response = requests.get(f"{BASE_URL}/users/search")

    assert response.status_code == 401, response.text