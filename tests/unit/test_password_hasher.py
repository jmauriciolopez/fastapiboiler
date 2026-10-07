"""Unit tests for the Argon2 password hasher adapter."""

import pytest

from infrastructure.security.password_hasher import Argon2PasswordHasher


@pytest.mark.asyncio
async def test_hash_and_verify_round_trip() -> None:
    hasher = Argon2PasswordHasher()
    password = "un-secreto-seguro"

    hashed_password = await hasher.hash(password)

    assert hashed_password != password
    assert await hasher.verify(password, hashed_password) is True


@pytest.mark.asyncio
async def test_verify_rejects_a_wrong_password() -> None:
    hasher = Argon2PasswordHasher()
    hashed_password = await hasher.hash("un-secreto-seguro")

    assert await hasher.verify("otra-clave", hashed_password) is False


@pytest.mark.asyncio
async def test_verify_returns_false_for_an_unknown_hash_format() -> None:
    hasher = Argon2PasswordHasher()

    assert await hasher.verify("un-secreto-seguro", "no-es-un-hash-valido") is False
