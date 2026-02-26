# Pytest configuration
# tests/conftest.py

import asyncio
import pytest
from database.engine import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    asyncio.run(init_db())
