class DomainException(Exception):
    """Base class for domain-level exceptions."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EntityNotFoundException(DomainException):
    def __init__(self, message: str = "Recurso no encontrado") -> None:
        super().__init__(message)


class DomainValidationException(DomainException):
    pass


class DomainConflictException(DomainException):
    pass
