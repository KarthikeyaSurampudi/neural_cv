import asyncio
import os
import sys

# Add the project directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.engine import get_db_session
from sqlalchemy import text

async def check():
    async with get_db_session() as session:
        result = await session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user' OR table_name = 'analysis' OR table_name = 'candidate';
        """))
        for row in result.fetchall():
            print(f"{row[0]}: {row[1]}")

if __name__ == "__main__":
    asyncio.run(check())
