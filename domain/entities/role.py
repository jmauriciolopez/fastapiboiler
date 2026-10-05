from dataclasses import dataclass

from shared.domain.entities import AuditableEntity


@dataclass(kw_only=True)
class Role(AuditableEntity):
    name: str
