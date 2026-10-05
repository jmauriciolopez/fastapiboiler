from shared.domain.exceptions import DomainException


class AuthException(DomainException):
    """Base exception for authentication errors."""


class InvalidCredentialsException(AuthException):
    def __init__(self, message: str = "Invalid username or password") -> None:
        super().__init__(message)


class InvalidTokenException(AuthException):
    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(message)
