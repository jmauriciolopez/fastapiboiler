"""Pruebas unitarias del servicio de tokens JWT."""

import pytest

from domain.exceptions.auth_exceptions import InvalidTokenException
from infrastructure.security.token_service import JwtTokenService


def test_token_round_trip_returns_the_original_claims() -> None:
    service = JwtTokenService("clave-de-prueba")

    token = service.generate_token({"sub": "123", "username": "ada"})
    claims = service.decode_token(token)

    assert claims["sub"] == "123"
    assert claims["username"] == "ada"
    assert claims["exp"] > claims["iat"]


def test_decode_rejects_a_token_signed_with_another_secret() -> None:
    token = JwtTokenService("clave-a").generate_token({"sub": "123"})

    with pytest.raises(InvalidTokenException, match="firma"):
        JwtTokenService("clave-b").decode_token(token)


def test_decode_rejects_a_malformed_token() -> None:
    with pytest.raises(InvalidTokenException, match="formato"):
        JwtTokenService("clave-de-prueba").decode_token("no-es-un-token")


def test_decode_rejects_a_tampered_payload() -> None:
    service = JwtTokenService("clave-de-prueba")
    header, payload, signature = service.generate_token({"sub": "123"}).split(".")

    with pytest.raises(InvalidTokenException, match="firma"):
        service.decode_token(f"{header}.{payload[:-2]}XY.{signature}")


def test_decode_rejects_an_expired_token() -> None:
    service = JwtTokenService("clave-de-prueba", expires_minutes=-1)

    with pytest.raises(InvalidTokenException, match="expirado"):
        service.decode_token(service.generate_token({"sub": "123"}))


def test_empty_secret_is_rejected() -> None:
    with pytest.raises(ValueError, match="secreto"):
        JwtTokenService("")
