"""Pruebas unitarias de la clase base de servicios."""

from shared.application.base_service import BaseService
from tests.fakes import InMemoryRepository


def test_base_service_delegates_domain_objects_to_repository() -> None:
    repository: InMemoryRepository[str] = InMemoryRepository()
    service = BaseService(repository)

    assert service.create("example") == "example"
    assert service.get_by_id(1) == "example"
    assert service.list_all() == ["example"]
    assert service.list_page(limit=1, offset=0).total == 1
