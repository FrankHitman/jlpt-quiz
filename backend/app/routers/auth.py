"""用戶註冊 / 登入 / 當前用戶。密碼用 bcrypt 存儲，登入發 JWT。"""
from __future__ import annotations

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import create_access_token, get_current_user
from ..db import get_db

router = APIRouter()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _issue(user: models.User) -> schemas.AuthOut:
    assert user.username is not None
    return schemas.AuthOut(
        token=create_access_token(user.id, user.username),
        user=schemas.UserOut(id=user.id, username=user.username),
    )


@router.post("/auth/register", response_model=schemas.AuthOut)
def register(payload: schemas.AuthIn, db: Session = Depends(get_db)):
    username = payload.username.strip()
    if len(username) < 3 or len(username) > 32:
        raise HTTPException(
            status_code=400, detail="用戶名需為 3–32 個字元"
        )
    exists = db.query(models.User).filter_by(username=username).first()
    if exists is not None:
        raise HTTPException(status_code=400, detail="該用戶名已被註冊")
    user = models.User(username=username, password_hash=_hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue(user)


@router.post("/auth/login", response_model=schemas.AuthOut)
def login(payload: schemas.AuthIn, db: Session = Depends(get_db)):
    username = payload.username.strip()
    user = db.query(models.User).filter_by(username=username).first()
    if user is None or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶名或密碼錯誤",
        )
    return _issue(user)


@router.get("/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    assert user.username is not None
    return schemas.UserOut(id=user.id, username=user.username)
