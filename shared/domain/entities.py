# domain/entities.py
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class BaseEntity:
    """Clase que representa a un id en la entidad."""
    id: UUID = field(default_factory=uuid4)

@dataclass
class AuditableEntity(BaseEntity):
    """Clase que representa a una entidad auditable."""
    created_on: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_on: datetime | None = None
    deleted: bool = False

# @dataclass
# class User(AuditableEntity):
#     name: str
#     email: str
