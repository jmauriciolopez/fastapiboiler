from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from application.ports.password_hasher import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self.password_hash = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self.password_hash.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        try:
            return self.password_hash.verify(password, hashed_password)
        except UnknownHashError:
            return False
