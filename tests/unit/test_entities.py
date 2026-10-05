"""Pruebas unitarias de las entidades de dominio."""

from domain.entities.role import Role
from domain.entities.user import User, UserStatus


def test_user_defaults_to_pending_status_and_stores_hashed_password() -> None:
    user = User(
        username="Ada",
        email="ada@example.com",
        phone="555-0100",
        hashed_password="encoded-password-hash",
    )

    assert user.status is UserStatus.PENDING
    assert user.hashed_password == "encoded-password-hash"
    assert not hasattr(user, "password")


def test_user_status_enum_values() -> None:
    assert {status.value for status in UserStatus} == {
        "pending",
        "active",
        "inactive",
        "blocked",
    }


def test_user_can_have_multiple_roles() -> None:
    roles = [Role(name="admin"), Role(name="editor")]
    user = User(
        username="Ada",
        email="ada@example.com",
        phone="555-0100",
        hashed_password="encoded-password-hash",
        roles=roles,
    )

    assert user.roles == roles
    assert [role.name for role in user.roles] == ["admin", "editor"]


def test_users_get_independent_role_lists_by_default() -> None:
    first_user = User(username="Ada", email="ada@example.com", phone="555-0100", hashed_password="hash-a")
    second_user = User(username="Grace", email="grace@example.com", phone="555-0101", hashed_password="hash-b")

    first_user.roles.append(Role(name="admin"))

    assert len(first_user.roles) == 1
    assert second_user.roles == []


def test_role_generates_id_and_audit_timestamp() -> None:
    role = Role(name="admin")

    assert role.id is not None
    assert role.created_on.tzinfo is not None
    assert role.updated_on is None
    assert role.deleted is False
