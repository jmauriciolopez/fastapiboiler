"""Unit tests for the JWT token service backed by PyJWT."""

import pytest

from domain.exceptions.auth_exceptions import InvalidTokenException
from infrastructure.security.token_service import JwtTokenService


def test_token_round_trip_returns_the_original_claims() -> None:
    service = JwtTokenService("clave-de-prueba-suficientemente-larga-32-chars")

    token = service.generate_token({"sub": "123", "username": "ada"})
    claims = service.decode_token(token)

    assert claims["sub"] == "123"
    assert claims["username"] == "ada"
    assert claims["exp"] > claims["iat"]


def test_decode_rejects_a_token_signed_with_another_secret() -> None:
    token = JwtTokenService("clave-a-suficientemente-larga-para-hmac256").generate_token({"sub": "123"})

    with pytest.raises(InvalidTokenException):
        JwtTokenService("clave-b-suficientemente-larga-para-hmac256").decode_token(token)


def test_decode_rejects_a_malformed_token() -> None:
    with pytest.raises(InvalidTokenException):
        JwtTokenService("clave-de-prueba-suficientemente-larga-32-chars").decode_token("no-es-un-token")


def test_decode_rejects_a_tampered_payload() -> None:
    service = JwtTokenService("clave-de-prueba-suficientemente-larga-32-chars")
    header, payload, signature = service.generate_token({"sub": "123"}).split(".")

    with pytest.raises(InvalidTokenException):
        service.decode_token(f"{header}.{payload[:-2]}XY.{signature}")


def test_decode_rejects_an_expired_token() -> None:
    service = JwtTokenService("clave-de-prueba-suficientemente-larga-32-chars", expires_minutes=-1)

    with pytest.raises(InvalidTokenException):
        service.decode_token(service.generate_token({"sub": "123"}))


def test_empty_secret_is_rejected() -> None:
    with pytest.raises(ValueError, match="secreto"):
        JwtTokenService("")
