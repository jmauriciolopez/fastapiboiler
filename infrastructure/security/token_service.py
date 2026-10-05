"""Implementación HS256 de tokens JWT usando solo la librería estándar.

Se implementa a mano para no añadir una dependencia externa. En producción es
preferible una librería auditada (por ejemplo ``pyjwt``): el contrato de
``TokenServicePort`` no cambia, solo esta clase.

El algoritmo se fija en HS256 y la firma se verifica *antes* de leer la
cabecera, para que un token con ``alg`` manipulado no pueda influir en la
verificación.
"""

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

from application.ports.token_service import TokenPayload, TokenServicePort
from domain.exceptions.auth_exceptions import InvalidTokenException

_ALGORITHM = "HS256"


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


class JwtTokenService(TokenServicePort):
    """Emite y valida tokens JWT firmados con HMAC-SHA256."""

    def __init__(self, secret_key: str, expires_minutes: int = 60) -> None:
        if not secret_key:
            raise ValueError("El secreto del token no puede estar vacío.")
        self.secret_key = secret_key.encode("utf-8")
        self.expires_minutes = expires_minutes

    def generate_token(self, payload: TokenPayload) -> str:
        issued_at = datetime.now(UTC)
        claims: TokenPayload = {
            **payload,
            "iat": int(issued_at.timestamp()),
            "exp": int((issued_at + timedelta(minutes=self.expires_minutes)).timestamp()),
        }
        signing_input = f"{self._encode_segment({'alg': _ALGORITHM, 'typ': 'JWT'})}.{self._encode_segment(claims)}"
        return f"{signing_input}.{self._sign(signing_input)}"

    def decode_token(self, token: str) -> TokenPayload:
        segments = token.split(".")
        if len(segments) != 3:
            raise InvalidTokenException("El token no tiene el formato esperado.")

        header_segment, payload_segment, signature_segment = segments
        signing_input = f"{header_segment}.{payload_segment}"

        if not hmac.compare_digest(self._sign(signing_input), signature_segment):
            raise InvalidTokenException("La firma del token no es válida.")

        if self._decode_segment(header_segment).get("alg") != _ALGORITHM:
            raise InvalidTokenException("El algoritmo del token no está permitido.")

        claims = self._decode_segment(payload_segment)
        self._validate_expiration(claims)
        return claims

    def _sign(self, signing_input: str) -> str:
        digest = hmac.new(self.secret_key, signing_input.encode("ascii"), hashlib.sha256).digest()
        return _b64url_encode(digest)

    def _encode_segment(self, content: TokenPayload) -> str:
        serialized = json.dumps(content, separators=(",", ":"), sort_keys=True)
        return _b64url_encode(serialized.encode("utf-8"))

    def _decode_segment(self, segment: str) -> TokenPayload:
        try:
            decoded = json.loads(_b64url_decode(segment))
        except ValueError as exc:
            raise InvalidTokenException("El token no se puede decodificar.") from exc
        if not isinstance(decoded, dict):
            raise InvalidTokenException("El contenido del token no es válido.")
        return decoded

    def _validate_expiration(self, claims: TokenPayload) -> None:
        expires_at = claims.get("exp")
        if not isinstance(expires_at, int):
            raise InvalidTokenException("El token no indica su expiración.")
        if datetime.now(UTC).timestamp() >= expires_at:
            raise InvalidTokenException("El token ha expirado.")
