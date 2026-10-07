"""Argon2 password hasher — CPU-bound work is offloaded to a thread pool
so it never blocks the asyncio event loop.
"""

import asyncio
from functools import partial

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from application.ports.password_hasher import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()

    async def hash(self, password: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._password_hash.hash, password)

    async def verify(self, password: str, hashed_password: str) -> bool:
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None,
                partial(self._password_hash.verify, password, hashed_password),
            )
        except UnknownHashError:
            return False
