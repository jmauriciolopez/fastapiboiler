"""Pruebas de los esquemas HTTP y de los mixins compartidos entre ellos."""

import pytest
from pydantic import ValidationError

from infrastructure.api.schemas.role_schemas import RoleCreate, RoleResponse
from infrastructure.api.schemas.user_schemas import UserCreate, UserUpdate

DUPLICATED_ROLE_ID = "00000000-0000-0000-0000-000000000001"


def _user_create_payload(**overrides: object) -> dict[str, object]:
    return {
        "username": "Ada",
        "email": "ada@example.com",
        "phone": "555-0100",
        "password": "un-secreto-seguro",
        **overrides,
    }


def _user_update_payload(**overrides: object) -> dict[str, object]:
    return {**_user_create_payload(), "status": "active", **overrides}


def test_role_schemas_use_the_domain_field_name() -> None:
    assert RoleCreate(name="admin").name == "admin"
    assert set(RoleResponse.model_fields) == {"id", "name"}


@pytest.mark.parametrize(
    ("schema", "payload"),
    [
        (UserCreate, _user_create_payload()),
        (UserUpdate, _user_update_payload()),
    ],
)
def test_user_schemas_share_the_duplicated_role_ids_validator(
    schema: type[UserCreate] | type[UserUpdate],
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError, match="No se permiten roles duplicados"):
        schema.model_validate({**payload, "role_ids": [DUPLICATED_ROLE_ID, DUPLICATED_ROLE_ID]})
