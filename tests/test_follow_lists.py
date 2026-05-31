import uuid

import requests


BASE_URL = "http://localhost:8000"
PASSWORD = "zaq1@WSX"


def register_user(email: str, first_name: str):
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "first_name": first_name,
            "last_name": "FollowList",
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


def follow_user(follower_headers: dict, followed_id: int):
    response = requests.post(
        f"{BASE_URL}/users/{followed_id}/follow",
        headers=follower_headers,
    )

    assert response.status_code == 201, response.text


def test_user_following_and_followers_lists():
    unique = uuid.uuid4().hex

    viewer = register_user(f"follow_lists_viewer_{unique}@student.pwr.edu.pl", "Viewer")
    user_a = register_user(f"follow_lists_a_{unique}@student.pwr.edu.pl", "UserA")
    user_b = register_user(f"follow_lists_b_{unique}@student.pwr.edu.pl", "UserB")
    user_c = register_user(f"follow_lists_c_{unique}@student.pwr.edu.pl", "UserC")

    viewer_headers = login_user(viewer["email"])
    user_a_headers = login_user(user_a["email"])
    user_c_headers = login_user(user_c["email"])

    follow_user(user_a_headers, user_b["id"])
    follow_user(user_a_headers, user_c["id"])
    follow_user(user_c_headers, user_a["id"])

    following_response = requests.get(
        f"{BASE_URL}/users/{user_a['id']}/following",
        headers=viewer_headers,
    )

    assert following_response.status_code == 200, following_response.text

    following = following_response.json()
    following_ids = {user["id"] for user in following}

    assert user_b["id"] in following_ids
    assert user_c["id"] in following_ids
    assert user_a["id"] not in following_ids

    followers_response = requests.get(
        f"{BASE_URL}/users/{user_a['id']}/followers",
        headers=viewer_headers,
    )

    assert followers_response.status_code == 200, followers_response.text

    followers = followers_response.json()
    follower_ids = {user["id"] for user in followers}

    assert user_c["id"] in follower_ids
    assert user_b["id"] not in follower_ids
    assert user_a["id"] not in follower_ids

    sample_following_user = next(user for user in following if user["id"] == user_b["id"])

    assert sample_following_user["first_name"] == "UserB"
    assert sample_following_user["last_name"] == "FollowList"
    assert sample_following_user["university"] == "PWR"
    assert sample_following_user["faculty"] == "WIT"
    assert "avatar_url" in sample_following_user


def test_follow_lists_require_authentication():
    unique = uuid.uuid4().hex

    user = register_user(f"follow_lists_auth_{unique}@student.pwr.edu.pl", "AuthUser")

    following_response = requests.get(f"{BASE_URL}/users/{user['id']}/following")
    followers_response = requests.get(f"{BASE_URL}/users/{user['id']}/followers")

    assert following_response.status_code == 401
    assert followers_response.status_code == 401


def test_follow_lists_return_404_for_missing_user():
    unique = uuid.uuid4().hex

    viewer = register_user(f"follow_lists_missing_viewer_{unique}@student.pwr.edu.pl", "Viewer")
    viewer_headers = login_user(viewer["email"])

    missing_user_id = 999999999

    following_response = requests.get(
        f"{BASE_URL}/users/{missing_user_id}/following",
        headers=viewer_headers,
    )
    followers_response = requests.get(
        f"{BASE_URL}/users/{missing_user_id}/followers",
        headers=viewer_headers,
    )

    assert following_response.status_code == 404
    assert followers_response.status_code == 404