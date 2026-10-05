"""Pruebas de integración del login y del acceso con token."""

from typing import cast

from fastapi.testclient import TestClient
from httpx import Response

VALID_PASSWORD = "un-secreto-seguro"


def _create_user(client: TestClient, username: str = "ada") -> Response:
    return cast(
        Response,
        client.post(
            "/api/v1/users/",
            json={
                "username": username,
                "email": f"{username.lower()}@example.com",
                "phone": "+1-555-0100",
                "password": VALID_PASSWORD,
                "role_ids": [],
            },
        ),
    )


def _login(client: TestClient, username: str, password: str) -> Response:
    return cast(
        Response,
        client.post("/api/v1/auth/login", json={"username": username, "password": password}),
    )


def _authorization_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_returns_a_token_that_identifies_the_user(client: TestClient) -> None:
    created_user = _create_user(client).json()

    response = _login(client, "ada", VALID_PASSWORD)

    assert response.status_code == 200
    token_body = response.json()
    assert token_body["token_type"] == "bearer"

    me = client.get("/api/v1/auth/me", headers=_authorization_header(token_body["access_token"]))

    assert me.status_code == 200
    assert me.json()["id"] == created_user["id"]
    assert me.json()["username"] == "ada"
    assert "hashed_password" not in me.json()


def test_login_is_case_insensitive_on_username(client: TestClient) -> None:
    assert _create_user(client, username="Ada").status_code == 201

    assert _login(client, "ada", VALID_PASSWORD).status_code == 200


def test_login_rejects_a_wrong_password(client: TestClient) -> None:
    _create_user(client)

    response = _login(client, "ada", "clave-incorrecta")

    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "invalid_credentials", "message": "Invalid username or password"}
    }


def test_login_rejects_an_unknown_username(client: TestClient) -> None:
    response = _login(client, "nadie", VALID_PASSWORD)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_current_user_requires_a_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_current_user_rejects_a_token_that_is_not_valid(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers=_authorization_header("token-invalido"))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_current_user_rejects_a_token_of_a_deleted_user(client: TestClient) -> None:
    created_user = _create_user(client).json()
    token = _login(client, "ada", VALID_PASSWORD).json()["access_token"]

    assert client.delete(f"/api/v1/users/{created_user['id']}").status_code == 204

    response = client.get("/api/v1/auth/me", headers=_authorization_header(token))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"
