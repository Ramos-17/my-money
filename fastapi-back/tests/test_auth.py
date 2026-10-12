from datetime import datetime, timedelta
from jose import jwt
from security import SECRET_KEY, ALGORITHM


def test_signup_with_valid_data_returns_201(client):
    response = client.post("/auth/register", json={
        "username": "newuser",
        "password": "securepass123",
        "email": "newuser@example.com",
        "first": "New",
        "last": "User",
    })

    assert response.status_code == 201
    data = response.json()
    assert "password_hash" not in data
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["first"] == "New"
    assert data["last"] == "User"
    assert "id" in data
    assert "created" in data


def test_signup_with_duplicate_email_returns_400(client, create_user):
    create_user(username="original", email="taken@example.com")

    response = client.post("/auth/register", json={
        "username": "different",
        "password": "securepass123",
        "email": "taken@example.com",
        "first": "New",
        "last": "User",
    })

    assert response.status_code == 400


def test_signup_with_duplicate_username_returns_400(client, create_user):
    create_user(username="taken", email="original@example.com")

    response = client.post("/auth/register", json={
        "username": "taken",
        "password": "securepass123",
        "email": "different@example.com",
        "first": "New",
        "last": "User",
    })

    assert response.status_code == 400


def test_login_with_correct_credentials_returns_200_and_sets_cookie(client, create_user):
    create_user(username="loginuser", password="correctpass")

    response = client.post("/auth/login", json={"username": "loginuser", "password": "correctpass"})

    assert response.status_code == 200
    assert "access_token" in response.cookies


def test_login_with_wrong_password_returns_401(client, create_user):
    create_user(username="loginuser", password="correctpass")

    response = client.post("/auth/login", json={"username": "loginuser", "password": "wrongpass"})

    assert response.status_code == 401


def test_login_with_nonexistent_username_returns_401_with_same_message_as_wrong_password(client, create_user):
    create_user(username="loginuser", password="correctpass")

    wrong_password_response = client.post("/auth/login", json={"username": "loginuser", "password": "wrongpass"})
    nonexistent_user_response = client.post("/auth/login", json={"username": "ghostuser", "password": "whatever"})

    assert nonexistent_user_response.status_code == 401
    assert nonexistent_user_response.json()["detail"] == wrong_password_response.json()["detail"]


def test_get_me_with_valid_token_returns_200_and_correct_user(auth_client):
    client, user = auth_client

    response = client.get("/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user.id)
    assert data["username"] == user.username
    assert data["email"] == user.email


def test_get_me_with_no_token_returns_401(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_get_me_with_invalid_token_returns_401(client):
    client.cookies.set("access_token", "not-a-real-token")

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_get_me_with_expired_token_returns_401(client, create_user):
    user = create_user(username="expireduser")
    expired_token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.utcnow() - timedelta(minutes=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    client.cookies.set("access_token", expired_token)

    response = client.get("/auth/me")

    assert response.status_code == 401
