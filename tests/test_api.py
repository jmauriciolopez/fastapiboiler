from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domain.entities.role import Role
from infrastructure.api.schemas.role_schemas import RoleCreate
from main import app
from shared.application.base_service import BaseService
from shared.application.pagination import PaginatedResult
from shared.domain.base_repository import BaseRepository
from shared.domain.exceptions import (
    DomainConflictException,
    DomainValidationException,
    EntityNotFoundException,
)
from shared.infrastructure.database import Base, _normalize_database_url, get_db
from shared.infrastructure.exceptions import register_exception_handlers
from shared.infrastructure.generic_controller import create_generic_router


class InMemoryRepository(BaseRepository[str]):
    def __init__(self) -> None:
        self.entities: dict[int | UUID, str] = {}
        self.deleted: set[int | UUID] = set()

    def save(self, entity: str) -> str:
        self.entities[len(self.entities) + 1] = entity
        return entity

    def get_by_id(self, entity_id: int | UUID) -> str | None:
        if entity_id in self.deleted:
            raise EntityNotFoundException(f"Recurso con ID {entity_id} no existe.")
        return self.entities.get(entity_id)

    def get_all(self) -> list[str]:
        return [entity for entity_id, entity in self.entities.items() if entity_id not in self.deleted]

    def get_page(self, limit: int, offset: int) -> PaginatedResult[str]:
        items = self.get_all()
        return PaginatedResult(items[offset : offset + limit], len(items), limit, offset)

    def update(self, entity_id: int | UUID, entity: str) -> str:
        if entity_id in self.deleted or entity_id not in self.entities:
            raise EntityNotFoundException(f"Recurso con ID {entity_id} no existe.")
        self.entities[entity_id] = entity
        return entity

    def soft_delete(self, entity_id: int | UUID) -> None:
        self.deleted.add(entity_id)


class PayloadSchema(BaseModel):
    name: str


class DictionaryRepository(BaseRepository[dict[str, str]]):
    def __init__(self) -> None:
        self.entities: dict[int | UUID, dict[str, str]] = {}
        self.deleted: set[int | UUID] = set()

    def save(self, entity: dict[str, str]) -> dict[str, str]:
        self.entities[len(self.entities) + 1] = entity
        return entity

    def get_by_id(self, entity_id: int | UUID) -> dict[str, str] | None:
        if entity_id in self.deleted:
            raise EntityNotFoundException(f"Recurso con ID {entity_id} no existe.")
        return self.entities.get(entity_id)

    def get_all(self) -> list[dict[str, str]]:
        return [entity for entity_id, entity in self.entities.items() if entity_id not in self.deleted]

    def get_page(self, limit: int, offset: int) -> PaginatedResult[dict[str, str]]:
        items = self.get_all()
        return PaginatedResult(items[offset : offset + limit], len(items), limit, offset)

    def update(self, entity_id: int | UUID, entity: dict[str, str]) -> dict[str, str]:
        if entity_id in self.deleted or entity_id not in self.entities:
            raise EntityNotFoundException(f"Recurso con ID {entity_id} no existe.")
        self.entities[entity_id] = entity
        return entity

    def soft_delete(self, entity_id: int | UUID) -> None:
        self.deleted.add(entity_id)


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
    assert response.json() == {"error": {"code": "not_found", "message": "No encontrado"}}


@pytest.mark.parametrize(
    ("exception", "expected_status", "expected_code"),
    [
        (DomainValidationException("Regla inválida"), 422, "domain_validation_error"),
        (DomainConflictException("Conflicto"), 409, "conflict"),
    ],
)
def test_domain_errors_are_mapped_to_consistent_http_responses(
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    exception_app = FastAPI()
    register_exception_handlers(exception_app)

    @exception_app.get("/domain-error")
    def raise_domain_error() -> None:
        raise exception

    response = TestClient(exception_app).get("/domain-error")

    assert response.status_code == expected_status
    assert response.json() == {
        "error": {"code": expected_code, "message": str(exception)}
    }


def test_base_service_delegates_domain_objects_to_repository() -> None:
    repository = InMemoryRepository()
    service = BaseService(repository)

    assert service.create("example") == "example"
    assert service.get_by_id(1) == "example"
    assert service.list_all() == ["example"]


def test_generic_router_validates_request_schema_and_creates_domain_object() -> None:
    repository = DictionaryRepository()

    def get_service() -> BaseService[dict[str, str]]:
        return BaseService(repository)

    router = create_generic_router(
        get_service,
        PayloadSchema,
        lambda payload: payload.model_dump(),
        PayloadSchema,
        lambda entity_id, payload: payload.model_dump(),
        "recurso",
        PayloadSchema,
    )
    generic_app = FastAPI()
    register_exception_handlers(generic_app)
    generic_app.include_router(router, prefix="/resources")

    response = TestClient(generic_app).post("/resources/", json={"name": "example"})

    assert response.status_code == 201
    assert response.json() == {"name": "example"}
    client = TestClient(generic_app)
    assert client.get("/resources/1").json() == {"name": "example"}
    assert client.get("/resources/?limit=1&offset=0").json() == {
        "items": [{"name": "example"}],
        "total": 1,
        "limit": 1,
        "offset": 0,
    }
    assert client.put("/resources/1", json={"name": "updated"}).json() == {"name": "updated"}
    assert client.delete("/resources/1").status_code == 204
    assert client.get("/resources/").json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }
    assert client.get("/resources/1").status_code == 404
    assert client.put("/resources/1", json={"name": "again"}).status_code == 404


def test_role_endpoints_use_database_and_expose_create_list_and_get() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine)

    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        create_response = client.post("/api/v1/roles/", json={"rol": "admin"})

        assert create_response.status_code == 201
        created_role = create_response.json()
        role_id = created_role["id"]
        assert created_role["rol"] == "admin"
        second_role = client.post("/api/v1/roles/", json={"rol": "reader"}).json()
        first_page = client.get("/api/v1/roles/?limit=1&offset=0").json()
        second_page = client.get("/api/v1/roles/?limit=1&offset=1").json()
        assert first_page == {"items": [created_role], "total": 2, "limit": 1, "offset": 0}
        assert second_page == {"items": [second_role], "total": 2, "limit": 1, "offset": 1}
        assert client.get(f"/api/v1/roles/{role_id}").json() == created_role
        update_response = client.put(f"/api/v1/roles/{role_id}", json={"rol": "operator"})
        assert update_response.status_code == 200
        assert update_response.json()["rol"] == "operator"
        delete_response = client.delete(f"/api/v1/roles/{role_id}")
        assert delete_response.status_code == 204
        assert client.get("/api/v1/roles/").json() == {
            "items": [second_role],
            "total": 1,
            "limit": 20,
            "offset": 0,
        }
        assert client.get(f"/api/v1/roles/{role_id}").status_code == 404
        assert client.put(f"/api/v1/roles/{role_id}", json={"rol": "restored"}).status_code == 404
        assert client.get("/api/v1/roles/00000000-0000-0000-0000-000000000000").status_code == 404
        assert client.post("/api/v1/roles/", json={}).status_code == 422
        assert client.put(f"/api/v1/roles/{role_id}", json={}).status_code == 422
        assert client.get("/api/v1/roles/not-a-uuid").status_code == 422
        assert client.get("/api/v1/roles/?limit=0").status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_role_model_and_schema_follow_existing_domain_model() -> None:
    role = Role(rol="admin")
    response_schema = RoleCreate.model_validate({"rol": role.rol})

    assert response_schema.rol == "admin"
    assert role.id is not None
    assert role.created_on.tzinfo is not None


def test_database_dependency_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        next(get_db())


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
def test_postgresql_urls_use_psycopg_driver(scheme: str) -> None:
    normalized_url = _normalize_database_url(f"{scheme}://user:password@localhost:5432/demo")

    assert normalized_url.startswith("postgresql+psycopg://")
