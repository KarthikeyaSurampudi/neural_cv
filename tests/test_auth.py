# Authentication tests

# tests/test_auth.py

import asyncio
import pytest

from services.user_service import create_user
from services.auth_service import authenticate_user


@pytest.mark.asyncio
async def test_user_authentication():

    user_id, error = await create_user(
        username="testuser",
        password="Password1",
        is_admin=False
    )

    assert user_id is not None
    assert error is None

    user, auth_error = await authenticate_user("testuser", "Password1")

    assert user is not None
    assert auth_error is None