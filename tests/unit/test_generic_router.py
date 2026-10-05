"""Pruebas unitarias del router genérico reutilizado por los controladores."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.application.base_service import BaseService
from shared.infrastructure.exceptions import register_exception_handlers
from shared.infrastructure.generic_controller import create_generic_router
from tests.fakes import (
    FakeLogger,
    InMemoryRepository,
    PayloadSchema,
    ValidatedPayloadSchema,
)


def test_generic_router_validates_request_schema_and_creates_domain_object() -> None:
    repository = InMemoryRepository[dict[str, str]]()

    def get_service() -> BaseService[dict[str, str]]:
        return BaseService(repository, FakeLogger())

    router = create_generic_router(
        get_service,
        ValidatedPayloadSchema,
        lambda payload: payload.model_dump(),
        ValidatedPayloadSchema,
        lambda entity_id, payload: payload.model_dump(),
        "recurso",
        PayloadSchema,
    )
    generic_app = FastAPI()
    register_exception_handlers(generic_app)
    generic_app.include_router(router, prefix="/resources")

    ValidatedPayloadSchema.validation_count = 0
    response = TestClient(generic_app).post("/resources/", json={"name": "example"})

    assert response.status_code == 201
    assert response.json() == {"name": "example"}
    assert ValidatedPayloadSchema.validation_count == 1

    client = TestClient(generic_app)
    assert client.get("/resources/1").json() == {"name": "example"}
    assert client.get("/resources/999").status_code == 404
    assert client.get("/resources/?limit=1&offset=0").json() == {
        "items": [{"name": "example"}],
        "total": 1,
        "limit": 1,
        "offset": 0,
    }

    ValidatedPayloadSchema.validation_count = 0
    assert client.put("/resources/1", json={"name": "updated"}).json() == {"name": "updated"}
    assert ValidatedPayloadSchema.validation_count == 1

    assert client.delete("/resources/1").status_code == 204
    assert client.get("/resources/").json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }
    assert client.get("/resources/1").status_code == 404
    assert client.put("/resources/1", json={"name": "again"}).status_code == 404
