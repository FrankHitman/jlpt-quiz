"""用戶註冊 / 登入 / 當前用戶。密碼用 bcrypt 存儲，登入發 JWT。

防護：註冊需郵箱＋圖形驗證碼；註冊/登入/驗證碼接口按 IP 限流。
"""
from __future__ import annotations

import re

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import create_access_token, get_current_user
from ..db import get_db
from ..security import (
    check_rate_limit,
    get_client_ip,
    new_captcha,
    verify_captcha,
)

router = APIRouter()

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


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
        user=schemas.UserOut(id=user.id, username=user.username, email=user.email),
    )


def _rate_limited(request: Request, scope: str, limit: int, window: int, msg: str) -> None:
    ip = get_client_ip(request)
    if not check_rate_limit(f"{scope}:{ip}", limit, window):
        raise HTTPException(status_code=429, detail=msg)


@router.get("/auth/captcha")
def captcha(request: Request):
    """取圖形驗證碼：30 次/分鐘/IP，5 分鐘有效，一次性使用。"""
    _rate_limited(request, "captcha", 30, 60, "請求過於頻繁，請稍後再試")
    captcha_id, image = new_captcha()
    return {"captcha_id": captcha_id, "image": image}


@router.post("/auth/register", response_model=schemas.AuthOut)
def register(
    payload: schemas.RegisterIn, request: Request, db: Session = Depends(get_db)
):
    # 單 IP 每小時最多註冊 5 個帳號（防惡意批量註冊）
    _rate_limited(request, "register", 5, 3600, "該 IP 註冊過於頻繁，請一小時後再試")

    if not verify_captcha(payload.captcha_id, payload.captcha_code):
        raise HTTPException(status_code=400, detail="驗證碼錯誤或已過期，請重新獲取")

    username = payload.username.strip()
    if len(username) < 3 or len(username) > 32:
        raise HTTPException(status_code=400, detail="用戶名需為 3–32 個字元")
    email = payload.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="郵箱地址格式不正確")

    if db.query(models.User).filter_by(username=username).first() is not None:
        raise HTTPException(status_code=400, detail="該用戶名已被註冊")
    if db.query(models.User).filter_by(email=email).first() is not None:
        raise HTTPException(status_code=400, detail="該郵箱已被註冊")

    user = models.User(
        username=username, email=email, password_hash=_hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue(user)


@router.post("/auth/login", response_model=schemas.AuthOut)
def login(payload: schemas.AuthIn, request: Request, db: Session = Depends(get_db)):
    # 單 IP 每 10 分鐘最多 30 次登入嘗試（防撞庫）
    _rate_limited(request, "login", 30, 600, "登入嘗試過於頻繁，請稍後再試")

    identifier = payload.username.strip()
    if "@" in identifier:
        user = db.query(models.User).filter_by(email=identifier.lower()).first()
    else:
        user = db.query(models.User).filter_by(username=identifier).first()
    if user is None or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶名/郵箱或密碼錯誤",
        )
    return _issue(user)


@router.get("/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    assert user.username is not None
    return schemas.UserOut(id=user.id, username=user.username, email=user.email)
