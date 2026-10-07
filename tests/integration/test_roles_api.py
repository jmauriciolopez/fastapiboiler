"""Integration tests for role endpoints and repository."""

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities.role import Role
from infrastructure.database.repositories.role_repository import RoleRepository
from shared.domain.exceptions import DomainConflictException


def test_role_endpoints_use_database_and_expose_create_list_and_get(
    client: TestClient,
) -> None:
    create_response = client.post("/api/v1/roles/", json={"name": "admin"})

    assert create_response.status_code == 201
    created_role = create_response.json()
    role_id = created_role["id"]
    assert created_role["name"] == "admin"
    assert client.post("/api/v1/roles/", json={"name": "ADMIN"}).status_code == 409

    second_role_response = client.post("/api/v1/roles/", json={"name": "reader"})
    assert second_role_response.status_code == 201
    second_role = second_role_response.json()

    first_page = client.get("/api/v1/roles/?limit=1&offset=0").json()
    second_page = client.get("/api/v1/roles/?limit=1&offset=1").json()
    assert first_page == {"items": [created_role], "total": 2, "limit": 1, "offset": 0}
    assert second_page == {"items": [second_role], "total": 2, "limit": 1, "offset": 1}
    assert client.get(f"/api/v1/roles/{role_id}").json() == created_role

    update_response = client.put(f"/api/v1/roles/{role_id}", json={"name": "operator"})
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "operator"

    patch_response = client.patch(f"/api/v1/roles/{role_id}", json={})
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "operator"
    patch_response = client.patch(f"/api/v1/roles/{role_id}", json={"name": "maintainer"})
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "maintainer"
    assert client.patch(f"/api/v1/roles/{role_id}", json={"name": None}).status_code == 422
    assert client.put(f"/api/v1/roles/{role_id}", json={"name": "reader"}).status_code == 409

    delete_response = client.delete(f"/api/v1/roles/{role_id}")
    assert delete_response.status_code == 204
    assert client.get("/api/v1/roles/").json() == {
        "items": [second_role],
        "total": 1,
        "limit": 20,
        "offset": 0,
    }
    assert client.get(f"/api/v1/roles/{role_id}").status_code == 404
    assert client.put(f"/api/v1/roles/{role_id}", json={"name": "restored"}).status_code == 404
    assert client.get("/api/v1/roles/00000000-0000-0000-0000-000000000000").status_code == 404
    assert client.post("/api/v1/roles/", json={}).status_code == 422
    assert client.put(f"/api/v1/roles/{role_id}", json={}).status_code == 422
    assert client.get("/api/v1/roles/not-a-uuid").status_code == 422
    assert client.get("/api/v1/roles/?limit=0").status_code == 422

    replacement_role = client.post("/api/v1/roles/", json={"name": "ADMIN"})
    assert replacement_role.status_code == 201


def test_role_repository_rolls_back_unique_conflict_and_session_can_continue(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def _run() -> None:
        async with session_factory() as db:
            repository = RoleRepository(db)

            await repository.save(Role(name="admin"))
            await db.commit()

            with pytest.raises(DomainConflictException, match="Ya existe un rol"):
                await repository.save(Role(name="ADMIN"))
                await db.commit()

            # Session should still be usable after the conflict
            saved_role = await repository.save(Role(name="reader"))
            await db.commit()
            assert saved_role.name == "reader"
            all_roles = await repository.get_all()
            assert len(all_roles) == 2

    asyncio.run(_run())
