# JWT handling

# auth/jwt_handler.py

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple

from jose import jwt, JWTError
from core.config import config

SECRET_KEY = config.jwt_secret_key

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY must be set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: str, username: str, is_admin: bool) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "username": username,
        "is_admin": is_admin,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_tokens(user_id: str, username: str, is_admin: bool) -> Tuple[str, str]:
    return (
        create_access_token(user_id, username, is_admin),
        create_refresh_token(user_id),
    )


def verify_token(token: str, expected_type: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[Dict]:
    return verify_token(token, "access")


def verify_refresh_token(token: str) -> Optional[Dict]:
    return verify_token(token, "refresh")


def is_token_expired(token: str) -> bool:
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return False
    except JWTError:
        return True