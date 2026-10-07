"""Unit tests for BaseService."""

import pytest

from shared.application.base_service import BaseService
from tests.fakes import FakeLogger, FakeUnitOfWork, InMemoryRepository


@pytest.mark.asyncio
async def test_base_service_delegates_domain_objects_to_repository() -> None:
    repository: InMemoryRepository[str] = InMemoryRepository()
    uow = FakeUnitOfWork()
    service: BaseService[str] = BaseService(repository, uow, FakeLogger())  # type: ignore[arg-type]

    saved = await service.create("example")
    assert saved == "example"
    assert await service.get_by_id(1) == "example"
    assert await service.list_all() == ["example"]
    page = await service.list_page(limit=1, offset=0)
    assert page.total == 1
