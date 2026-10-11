"""Auth placeholder.

`get_current_user_optional` is a FastAPI dependency used by all
/api/attempts* endpoints. Auth is NOT enabled yet:

- No Authorization header  -> returns None (never raises).
- Authorization header present but auth not enabled -> ignored, returns None.

When auth is enabled later, implement register/login in routers/auth.py
to issue tokens, and make this function validate the token and return the
user id.
"""
from __future__ import annotations

from fastapi import Header


def get_current_user_optional(
    authorization: str | None = Header(default=None),
) -> int | None:
    return None
