# Authentication service - Business logic

import bcrypt
from typing import Tuple, Optional, Dict
from database.repositories.user_repo import get_user_by_username


async def authenticate_user(username: str, password: str) -> Tuple[Optional[Dict], Optional[str]]:
    user = await get_user_by_username(username)
    if not user:
        return None, "Invalid username or password"

    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return None, "Invalid username or password"

    return user, None