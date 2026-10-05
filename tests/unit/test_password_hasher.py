"""Pruebas unitarias del adaptador de hashing de contraseñas."""

from infrastructure.security.password_hasher import Argon2PasswordHasher


def test_hash_and_verify_round_trip() -> None:
    hasher = Argon2PasswordHasher()
    password = "un-secreto-seguro"

    hashed_password = hasher.hash(password)

    assert hashed_password != password
    assert hasher.verify(password, hashed_password) is True


def test_verify_rejects_a_wrong_password() -> None:
    hasher = Argon2PasswordHasher()
    hashed_password = hasher.hash("un-secreto-seguro")

    assert hasher.verify("otra-clave", hashed_password) is False


def test_verify_returns_false_for_an_unknown_hash_format() -> None:
    hasher = Argon2PasswordHasher()

    assert hasher.verify("un-secreto-seguro", "no-es-un-hash-valido") is False
