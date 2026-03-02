import asyncio
import os
import sys
import bcrypt

# Add the project directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.engine import get_db_session
from database.models import User
from sqlalchemy import select

async def check():
    async with get_db_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"User: {u.username}")
            print(f"Hash: {u.password_hash}")
            # Try to check against the known password
            print(f"Matches 'Admin12345'?: {bcrypt.checkpw(b'Admin12345', u.password_hash.encode())}")
            print("---")

if __name__ == "__main__":
    asyncio.run(check())
