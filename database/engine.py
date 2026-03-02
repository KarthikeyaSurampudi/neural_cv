# Async engine + sessionmaker

# database/engine.py

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from core.config import config
from database.models import Base

# Dictionary to hold the engine for each specific asyncio event loop
_engines = {}

def get_engine():
    """
    Returns an AsyncEngine bound to the current asyncio event loop.
    This resolves Streamlit's thread-safety issues where scripts rerun
    in new threads/loops and hit 'attached to a different loop' errors.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop_id = id(loop)
    
    if loop_id not in _engines:
        _engines[loop_id] = create_async_engine(
            config.database_url,
            echo=False,
            future=True,
            pool_pre_ping=True, 
            pool_recycle=3600
        )
        
    return _engines[loop_id]


from contextlib import asynccontextmanager

async def init_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    engine = get_engine()
    AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_session():
    engine = get_engine()
    AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        yield session