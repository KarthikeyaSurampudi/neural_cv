import asyncio
import os
import sys

# Add the project directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.engine import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate():
    logger.info("Starting schema migration...")
    async with engine.begin() as conn:
        try:
            # User table
            await conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS failed_attempts INTEGER DEFAULT 0;'))
            await conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;'))
            await conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;'))

            # Candidate table
            await conn.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS summary TEXT;'))
            await conn.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS resume_hash VARCHAR(64);'))
            await conn.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS filename VARCHAR(500);'))
            await conn.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS was_cached BOOLEAN DEFAULT FALSE;'))
            
            # Analysis table
            await conn.execute(text('ALTER TABLE "analysis" ADD COLUMN IF NOT EXISTS stage2_count INTEGER DEFAULT 0;'))
            await conn.execute(text('ALTER TABLE "analysis" ADD COLUMN IF NOT EXISTS resume_set_hash VARCHAR(64);'))
            await conn.execute(text('ALTER TABLE "analysis" ADD COLUMN IF NOT EXISTS resume_files_info JSON;'))
            await conn.execute(text('ALTER TABLE "analysis" ADD COLUMN IF NOT EXISTS jd_file_path VARCHAR(500);'))

            # ScoreBreakdown table
            await conn.execute(text('ALTER TABLE "score_breakdown" ADD COLUMN IF NOT EXISTS rank INTEGER;'))
            await conn.execute(text('ALTER TABLE "score_breakdown" ADD COLUMN IF NOT EXISTS justification TEXT;'))
            
            logger.info("Successfully added missing columns to PostgreSQL tables.")
        except Exception as e:
            logger.error(f"Error during migration: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
