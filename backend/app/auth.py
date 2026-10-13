"""JWT 認證：註冊/登入發 token，各端點經由依賴取當前用戶。

- get_current_user_optional：可選認證。無 header → None；token 無效/用戶不存在 → None（不報錯）。
- get_current_user：必需認證。缺失或無效 → 401。
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from . import models
from .db import get_db

log = logging.getLogger(__name__)

_DEV_SECRET = "dev-jwt-secret-change-me"
_TOKEN_DAYS = 30
_warned = False


def get_jwt_secret() -> str:
    global _warned
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        if os.getenv("APP_ENV", "development") == "production":
            raise RuntimeError(
                "JWT_SECRET 未設置：生產環境（APP_ENV=production）拒絕使用開發預設密鑰，"
                "請設置強隨機的 JWT_SECRET 環境變數後再啟動。"
            )
        if not _warned:
            log.warning(
                "JWT_SECRET 未設置，使用開發預設值；生產環境務必設置強隨機密鑰。"
            )
            _warned = True
        secret = _DEV_SECRET
    return secret


def create_access_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": now + timedelta(days=_TOKEN_DAYS),
        "iat": now,
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def _decode_user_id(token: str) -> int | None:
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        uid = payload.get("user_id")
        return int(uid) if uid is not None else None
    except (jwt.PyJWTError, ValueError, TypeError):
        return None


def _bearer_user_id(authorization: str | None, db: Session) -> int | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    uid = _decode_user_id(token.strip())
    if uid is None:
        return None
    # token 合法但用戶已被刪除 → 視為未登入
    if db.get(models.User, uid) is None:
        return None
    return uid


def get_current_user_optional(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> int | None:
    """可選認證：合法 token 回 user_id，否則 None（永不報錯）。"""
    return _bearer_user_id(authorization, db)


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    """必需認證：回傳 User；缺失/無效 token 回 401。"""
    uid = _bearer_user_id(authorization, db)
    if uid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登入或登入已過期",
        )
    user = db.get(models.User, uid)
    if user is None:  # 理論上 _bearer_user_id 已排除
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶不存在",
        )
    return user
