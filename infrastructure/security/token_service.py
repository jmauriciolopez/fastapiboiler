"""JWT implementation backed by PyJWT (well-audited, actively maintained).

The algorithm is fixed to HS256 and only HS256 is accepted on decode,
preventing algorithm-confusion attacks (e.g. ``alg: none``).
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import PyJWTError

from application.ports.token_service import TokenPayload, TokenServicePort
from domain.exceptions.auth_exceptions import InvalidTokenException

_ALGORITHM = "HS256"


class JwtTokenService(TokenServicePort):
    """Issues and validates HS256-signed JWTs using PyJWT."""

    def __init__(self, secret_key: str, expires_minutes: int = 60) -> None:
        if not secret_key:
            raise ValueError("El secreto del token no puede estar vacío.")
        self._secret_key = secret_key
        self._expires_minutes = expires_minutes

    def generate_token(self, payload: TokenPayload) -> str:
        claims: dict[str, Any] = {
            **payload,
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(minutes=self._expires_minutes),
        }
        return jwt.encode(claims, self._secret_key, algorithm=_ALGORITHM)

    def decode_token(self, token: str) -> TokenPayload:
        try:
            return jwt.decode(
                token,
                self._secret_key,
                algorithms=[_ALGORITHM],  # whitelist only — prevents alg:none attacks
                options={"require": ["exp", "iat", "sub"]},
            )
        except PyJWTError as exc:
            raise InvalidTokenException(str(exc)) from exc
