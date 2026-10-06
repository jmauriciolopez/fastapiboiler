"""Pruebas de integración del CRUD genérico de productos."""

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.database.models.product_orm import ProductORM


def test_product_controller_exposes_generic_crud(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    create_response = client.post("/api/v1/products/", json={"name": "Keyboard"})

    assert create_response.status_code == 201
    created = create_response.json()
    product_id = UUID(created["id"])
    assert created == {"id": str(product_id), "name": "Keyboard"}

    with session_factory() as db:
        persisted = db.query(ProductORM).filter_by(id=product_id).one()
        assert persisted.name == "Keyboard"
        assert persisted.deleted is False

    listed = client.get("/api/v1/products/?limit=1&offset=0")
    assert listed.status_code == 200
    assert listed.json() == {
        "items": [created],
        "total": 1,
        "limit": 1,
        "offset": 0,
    }
    assert client.get(f"/api/v1/products/{product_id}").json() == created

    updated = client.put(f"/api/v1/products/{product_id}", json={"name": "Mechanical keyboard"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Mechanical keyboard"

    patched = client.patch(f"/api/v1/products/{product_id}", json={})
    assert patched.status_code == 200
    assert patched.json()["name"] == "Mechanical keyboard"

    patched = client.patch(
        f"/api/v1/products/{product_id}",
        json={"name": "Compact keyboard"},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Compact keyboard"
    assert client.patch(f"/api/v1/products/{product_id}", json={"name": None}).status_code == 422

    deleted = client.delete(f"/api/v1/products/{product_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/products/{product_id}").status_code == 404
    assert client.get("/api/v1/products/").json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }


def test_product_controller_validates_input_and_uuid(client: TestClient) -> None:
    assert client.post("/api/v1/products/", json={"name": ""}).status_code == 422
    assert client.post("/api/v1/products/", json={}).status_code == 422
    assert client.get("/api/v1/products/not-a-uuid").status_code == 422
