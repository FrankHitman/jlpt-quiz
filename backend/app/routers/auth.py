"""Auth placeholder endpoints — return 501 until auth is enabled."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/auth/register")
def register():
    raise HTTPException(status_code=501, detail="auth not enabled yet")


@router.post("/auth/login")
def login():
    raise HTTPException(status_code=501, detail="auth not enabled yet")
