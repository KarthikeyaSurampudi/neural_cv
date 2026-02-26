# User service - Business logic

# services/user_service.py

import uuid
import bcrypt
from typing import Optional, Tuple, Dict, List

from database.repositories.user_repo import (
    create_user as repo_create_user,
    get_user_by_id as repo_get_user_by_id,
    get_user_by_username as repo_get_user_by_username,
    list_users as repo_list_users,
    delete_user as repo_delete_user,
    update_password as repo_update_password
)


def _validate_password(password: str) -> Tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
    return True, ""


async def create_user(
    username: str,
    password: str,
    is_admin: bool = False
) -> Tuple[Optional[uuid.UUID], Optional[str]]:

    valid, error = _validate_password(password)
    if not valid:
        return None, error

    existing = await repo_get_user_by_username(username)
    if existing:
        return None, "Username already exists."

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user_id = await repo_create_user(
        username=username,
        password_hash=password_hash,
        is_admin=is_admin
    )

    return user_id, None


async def get_user(user_id: uuid.UUID) -> Optional[Dict]:
    return await repo_get_user_by_id(user_id)


async def list_users() -> List[Dict]:
    return await repo_list_users()


async def delete_user(user_id: uuid.UUID) -> bool:
    return await repo_delete_user(user_id)


async def change_password(
    user_id: uuid.UUID,
    current_password: str,
    new_password: str
) -> Tuple[bool, str]:

    user = await repo_get_user_by_id(user_id)
    if not user:
        return False, "User not found."

    if not bcrypt.checkpw(current_password.encode(), user["password_hash"].encode()):
        return False, "Incorrect current password."

    valid, error = _validate_password(new_password)
    if not valid:
        return False, error

    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    await repo_update_password(user_id, new_hash)

    return True, ""