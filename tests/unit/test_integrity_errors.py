"""Pruebas unitarias del clasificador de errores de integridad de SQLAlchemy."""

from sqlalchemy.exc import IntegrityError

from shared.infrastructure.integrity_errors import violates_unique_constraint


def test_integrity_error_is_only_classified_for_the_named_unique_index() -> None:
    email_conflict = IntegrityError(
        "INSERT INTO users",
        {},
        Exception("UNIQUE constraint failed: index 'uq_users_active_email_ci'"),
    )
    foreign_key_conflict = IntegrityError(
        "INSERT INTO users",
        {},
        Exception("FOREIGN KEY constraint failed"),
    )

    assert violates_unique_constraint(email_conflict, "uq_users_active_email_ci")
    assert not violates_unique_constraint(foreign_key_conflict, "uq_users_active_email_ci")
