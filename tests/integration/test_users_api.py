"""Pruebas de integración de los endpoints de usuarios."""

from uuid import UUID

from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.database.models.user_orm import UserORM
from infrastructure.database.repositories.user_repository import UserRepository


def test_user_endpoints_hash_passwords_and_manage_multiple_roles(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    password = "un-secreto-seguro"
    first_role = client.post("/api/v1/roles/", json={"name": "admin"}).json()
    second_role = client.post("/api/v1/roles/", json={"name": "editor"}).json()
    payload = {
        "username": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+1-555-0100",
        "password": password,
        "role_ids": [first_role["id"], second_role["id"]],
    }

    create_response = client.post("/api/v1/users/", json=payload)
    assert create_response.status_code == 201
    created_user = create_response.json()
    user_id = created_user["id"]
    assert created_user["status"] == "pending"
    assert {role["id"] for role in created_user["roles"]} == {
        first_role["id"],
        second_role["id"],
    }
    assert "password" not in created_user
    assert "hashed_password" not in created_user

    with session_factory() as db:
        persisted_user = db.query(UserORM).filter_by(id=UUID(user_id)).one()
        saved_hash = persisted_user.hashed_password
        assert saved_hash != password
        assert PasswordHash.recommended().verify(password, saved_hash)

    assert client.post("/api/v1/users/", json=payload).status_code == 409
    assert (
        client.post(
            "/api/v1/users/",
            json={**payload, "email": "ADA@example.com"},
        ).status_code
        == 409
    )

    invalid_role_payload = {
        **payload,
        "email": "other@example.com",
        "role_ids": ["00000000-0000-0000-0000-000000000000"],
    }
    assert client.post("/api/v1/users/", json=invalid_role_payload).status_code == 404

    listed_users = client.get("/api/v1/users/?limit=1&offset=0").json()
    assert listed_users["items"] == [created_user]
    assert listed_users["total"] == 1
    assert client.get(f"/api/v1/users/{user_id}").json() == created_user

    another_payload = {
        **payload,
        "username": "Grace Hopper",
        "email": "grace@example.com",
        "role_ids": [],
    }
    another_user = client.post("/api/v1/users/", json=another_payload).json()

    update_payload = {
        "username": "Ada Byron",
        "email": another_payload["email"],
        "phone": payload["phone"],
        "status": "active",
        "role_ids": [second_role["id"]],
    }
    assert client.put(f"/api/v1/users/{user_id}", json=update_payload).status_code == 409

    update_payload["email"] = payload["email"]
    update_response = client.put(f"/api/v1/users/{user_id}", json=update_payload)
    assert update_response.status_code == 200
    updated_user = update_response.json()
    assert updated_user["username"] == "Ada Byron"
    assert updated_user["status"] == "active"
    assert [role["id"] for role in updated_user["roles"]] == [second_role["id"]]

    with session_factory() as db:
        assert db.query(UserORM).filter_by(id=UUID(user_id)).one().hashed_password == saved_hash

    assert client.delete(f"/api/v1/users/{user_id}").status_code == 204
    assert client.delete(f"/api/v1/users/{another_user['id']}").status_code == 204
    assert client.get(f"/api/v1/users/{user_id}").status_code == 404
    assert client.get("/api/v1/users/").json()["total"] == 0

    reused_email_user = client.post("/api/v1/users/", json=payload)
    assert reused_email_user.status_code == 201


def test_user_repository_finds_users_by_username_and_hides_deleted_ones(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    created = client.post(
        "/api/v1/users/",
        json={
            "username": "ada",
            "email": "ada@example.com",
            "phone": "+1-555-0100",
            "password": "un-secreto-seguro",
            "role_ids": [],
        },
    ).json()

    with session_factory() as db:
        repository = UserRepository(db)

        found_user = repository.get_by_username("ada")
        assert found_user is not None
        assert found_user.username == "ada"
        assert repository.get_by_username("ADA") is not None
        assert repository.get_by_username("grace") is None

        repository.soft_delete(UUID(created["id"]))

        assert repository.get_by_username("ada") is None


def test_username_is_unique_among_active_users_and_reusable_after_deletion(
    client: TestClient,
) -> None:
    payload = {
        "username": "ada",
        "email": "ada@example.com",
        "phone": "+1-555-0100",
        "password": "un-secreto-seguro",
        "role_ids": [],
    }
    created = client.post("/api/v1/users/", json=payload)
    assert created.status_code == 201

    duplicated = client.post(
        "/api/v1/users/",
        json={**payload, "username": "ADA", "email": "otra@example.com"},
    )
    assert duplicated.status_code == 409
    assert duplicated.json()["code"] == "conflict"
    assert duplicated.json()["detail"] == (
        "Ya existe un usuario con ese nombre de usuario."
    )

    assert client.delete(f"/api/v1/users/{created.json()['id']}").status_code == 204

    reused = client.post(
        "/api/v1/users/",
        json={**payload, "email": "nueva@example.com"},
    )
    assert reused.status_code == 201


def test_patch_user_preserves_unprovided_fields_and_updates_roles(
    client: TestClient,
) -> None:
    first_role = client.post("/api/v1/roles/", json={"name": "member"}).json()
    second_role = client.post("/api/v1/roles/", json={"name": "admin"}).json()
    created = client.post(
        "/api/v1/users/",
        json={
            "username": "ada",
            "email": "ada@example.com",
            "phone": "+1-555-0100",
            "password": "un-secreto-seguro",
            "role_ids": [first_role["id"]],
        },
    ).json()

    patched = client.patch(
        f"/api/v1/users/{created['id']}",
        json={"username": "ada-lovelace", "role_ids": [second_role["id"]]},
    )

    assert patched.status_code == 200
    assert patched.json()["username"] == "ada-lovelace"
    assert patched.json()["email"] == "ada@example.com"
    assert patched.json()["phone"] == "+1-555-0100"
    assert patched.json()["status"] == "pending"
    assert [role["id"] for role in patched.json()["roles"]] == [second_role["id"]]
    assert client.patch(f"/api/v1/users/{created['id']}", json={"email": None}).status_code == 422


def test_patch_user_password_only_hashes_new_password_and_preserves_other_fields(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    old_password = "clave-anterior-segura"
    new_password = "clave-nueva-segura"
    role = client.post("/api/v1/roles/", json={"name": "password-patch-role"}).json()
    created = client.post(
        "/api/v1/users/",
        json={
            "username": "ada",
            "email": "ada@example.com",
            "phone": "+1-555-0100",
            "password": old_password,
            "role_ids": [role["id"]],
        },
    ).json()

    patched = client.patch(
        f"/api/v1/users/{created['id']}",
        json={"password": new_password},
    )

    assert patched.status_code == 200
    assert patched.json()["username"] == "ada"
    assert patched.json()["email"] == "ada@example.com"
    assert patched.json()["phone"] == "+1-555-0100"
    assert patched.json()["status"] == "pending"
    assert [saved_role["id"] for saved_role in patched.json()["roles"]] == [role["id"]]
    assert "password" not in patched.json()
    assert "hashed_password" not in patched.json()

    with session_factory() as db:
        persisted_user = db.query(UserORM).filter_by(id=UUID(created["id"])).one()
        assert persisted_user.hashed_password != old_password
        assert PasswordHash.recommended().verify(
            new_password,
            persisted_user.hashed_password,
        )
