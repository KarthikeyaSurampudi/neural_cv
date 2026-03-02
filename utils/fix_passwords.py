import asyncio
import os
import sys
import bcrypt

# Add the project directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.engine import get_db_session
from database.models import User
from sqlalchemy import select, update

async def fix():
    async with get_db_session() as session:
        # 1. Generate a new fresh hash
        salt = bcrypt.gensalt()
        new_hash = bcrypt.hashpw(b"Admin12345", salt).decode()
        
        # 2. Update the admin user
        await session.execute(
            update(User).where(User.username == 'admin').values(password_hash=new_hash)
        )
        await session.execute(
            update(User).where(User.username == 'admin2').values(password_hash=new_hash)
        )
        await session.commit()
        print("Successfully updated passwords for admin and admin2 to 'Admin12345'.")

if __name__ == "__main__":
    asyncio.run(fix())
