# User repository - DB access layer

# database/repositories/user_repo.py

import uuid
from typing import Optional, Dict, List

from sqlalchemy import select, delete, update
from database.engine import get_db_session
from database.models import User


async def create_user(username: str, password_hash: str, is_admin: bool) -> str:
    user_id = uuid.uuid4().hex
    async with get_db_session() as session:
        user = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            is_admin=is_admin,
            must_change_password=False,
            failed_attempts=0
        )
        session.add(user)
        await session.commit()
        return user_id


async def get_user_by_username(username: str) -> Optional[Dict]:
    async with get_db_session() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalars().first()
        if not user:
            return None
        return {
            "user_id": user.user_id,
            "username": user.username,
            "password_hash": user.password_hash,
            "is_admin": user.is_admin,
            "must_change_password": user.must_change_password,
            "failed_attempts": user.failed_attempts,
            "locked_until": user.locked_until
        }


async def get_user_by_id(user_id: str) -> Optional[Dict]:
    async with get_db_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalars().first()
        if not user:
            return None
        return {
            "user_id": user.user_id,
            "username": user.username,
            "password_hash": user.password_hash,
            "is_admin": user.is_admin,
            "must_change_password": user.must_change_password,
            "failed_attempts": user.failed_attempts,
            "locked_until": user.locked_until
        }


async def list_users() -> List[Dict]:
    async with get_db_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return [
            {
                "user_id": u.user_id,
                "username": u.username,
                "is_admin": u.is_admin,
                "must_change_password": u.must_change_password
            }
            for u in users
        ]


async def delete_user(user_id: str) -> bool:
    async with get_db_session() as session:
        await session.execute(
            delete(User).where(User.user_id == user_id)
        )
        await session.commit()
        return True


async def update_password(user_id: str, new_hash: str):
    async with get_db_session() as session:
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(password_hash=new_hash, must_change_password=False)
        )
        await session.commit()