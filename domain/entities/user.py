from dataclasses import dataclass, field
from enum import Enum

from domain.entities.role import Role
from shared.domain.entities import AuditableEntity


class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


@dataclass(kw_only=True)
class User(AuditableEntity):
    username: str
    email: str
    phone: str
    hashed_password: str
    status: UserStatus = UserStatus.PENDING
    roles: list[Role] = field(default_factory=list)
