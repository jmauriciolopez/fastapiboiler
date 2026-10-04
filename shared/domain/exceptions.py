class DomainException(Exception):
    """Base class for domain-level exceptions."""


class EntityNotFoundException(DomainException):
    def __init__(self, message: str = "Recurso no encontrado") -> None:
        self.message = message
        super().__init__(message)
