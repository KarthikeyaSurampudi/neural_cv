import asyncio
from services.user_service import create_user
from database.engine import init_db

async def setup():
    await init_db()
    user_id, error = await create_user(
        username="admin",
        password="Admin123",
        is_admin=True
    )
    print(user_id, error)

asyncio.run(setup())