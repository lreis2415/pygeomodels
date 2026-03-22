from contextvars import ContextVar
from typing import Optional


_bearer_token: ContextVar[Optional[str]] = ContextVar("bearer_token", default=None)


def set_bearer_token(token: Optional[str]) -> None:
    _bearer_token.set(token)


def get_bearer_token() -> Optional[str]:
    return _bearer_token.get()
