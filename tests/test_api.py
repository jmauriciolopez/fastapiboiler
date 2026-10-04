import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from main import app
from shared.application.base_service import BaseService
from shared.domain.base_repository import BaseRepository
from shared.domain.exceptions import EntityNotFoundException
from shared.infrastructure.database import get_db
from shared.infrastructure.exceptions import register_exception_handlers
from shared.infrastructure.generic_controller import create_generic_router


class InMemoryRepository(BaseRepository[str]):
    def __init__(self) -> None:
        self.entities: dict[int, str] = {}

    def save(self, entity: str) -> str:
        self.entities[len(self.entities) + 1] = entity
        return entity

    def get_by_id(self, entity_id: int) -> str | None:
        return self.entities.get(entity_id)

    def get_all(self) -> list[str]:
        return list(self.entities.values())


class PayloadSchema(BaseModel):
    name: str


class DictionaryRepository(BaseRepository[dict[str, str]]):
    def __init__(self) -> None:
        self.entities: dict[int, dict[str, str]] = {}

    def save(self, entity: dict[str, str]) -> dict[str, str]:
        self.entities[len(self.entities) + 1] = entity
        return entity

    def get_by_id(self, entity_id: int) -> dict[str, str] | None:
        return self.entities.get(entity_id)

    def get_all(self) -> list[dict[str, str]]:
        return list(self.entities.values())


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_existing_demo_routes_remain_available() -> None:
    client = TestClient(app)

    assert client.get("/").json() == {"mensaje": "¡Hola, mundo!"}
    assert client.get("/items/7?q=test").json() == {"item_id": 7, "q": "test"}


def test_domain_not_found_exception_is_mapped_to_404() -> None:
    exception_app = FastAPI()
    register_exception_handlers(exception_app)

    @exception_app.get("/missing")
    def missing() -> None:
        raise EntityNotFoundException("No encontrado")

    response = TestClient(exception_app).get("/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "No encontrado"}


def test_base_service_delegates_domain_objects_to_repository() -> None:
    repository = InMemoryRepository()
    service = BaseService(repository)

    assert service.create("example") == "example"
    assert service.get_by_id(1) == "example"
    assert service.list_all() == ["example"]


def test_generic_router_validates_request_schema_and_creates_domain_object() -> None:
    service = BaseService(DictionaryRepository())
    router = create_generic_router(
        service,
        PayloadSchema,
        lambda payload: payload.model_dump(),
        "recurso",
    )
    generic_app = FastAPI()
    generic_app.include_router(router, prefix="/resources")

    response = TestClient(generic_app).post("/resources/", json={"name": "example"})

    assert response.status_code == 201
    assert response.json() == {"name": "example"}


def test_database_dependency_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        next(get_db())
