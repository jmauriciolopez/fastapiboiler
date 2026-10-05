from sqlalchemy.exc import IntegrityError


def violates_unique_constraint(exc: IntegrityError, constraint_name: str) -> bool:
    original_error = exc.orig
    diagnostic = getattr(original_error, "diag", None)
    if getattr(diagnostic, "constraint_name", None) == constraint_name:
        return True
    return constraint_name in str(original_error)
