from typing import Any, Protocol

TokenPayload = dict[str, Any]


class TokenServicePort(Protocol):
    def generate_token(self, payload: TokenPayload) -> str: ...
    def decode_token(self, token: str) -> TokenPayload: ...
