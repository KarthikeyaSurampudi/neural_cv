import asyncio
import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.engine import get_db_session
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_all():
    logger.info("Starting comprehensive schema migration...")
    async with get_db_session() as session:
        # User
        await session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;'))
        await session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;'))
        
        # Candidate
        await session.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;'))
        await session.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;'))
        await session.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS summary TEXT;'))
        await session.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS resume_hash VARCHAR(64);'))
        await session.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS filename VARCHAR(500);'))
        await session.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS was_cached BOOLEAN DEFAULT FALSE;'))
        await session.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS skills_text TEXT;'))
        await session.execute(text('ALTER TABLE "candidate" ADD COLUMN IF NOT EXISTS experience_text TEXT;'))
        
        # Analysis
        await session.execute(text('ALTER TABLE "analysis" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;'))
        await session.execute(text('ALTER TABLE "analysis" ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;'))
        
        # Score Breakdown
        await session.execute(text('ALTER TABLE "score_breakdown" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;'))
        await session.execute(text('ALTER TABLE "score_breakdown" ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;'))
        await session.execute(text('ALTER TABLE "score_breakdown" ADD COLUMN IF NOT EXISTS rank INTEGER;'))
        await session.execute(text('ALTER TABLE "score_breakdown" ADD COLUMN IF NOT EXISTS justification TEXT;'))
        await session.execute(text('ALTER TABLE "score_breakdown" ADD COLUMN IF NOT EXISTS education_match FLOAT DEFAULT 0.0;'))
        await session.execute(text('ALTER TABLE "score_breakdown" ADD COLUMN IF NOT EXISTS exp_match FLOAT DEFAULT 0.0;'))
        await session.execute(text('ALTER TABLE "score_breakdown" ADD COLUMN IF NOT EXISTS skill_match FLOAT DEFAULT 0.0;'))
        await session.execute(text('ALTER TABLE "score_breakdown" ADD COLUMN IF NOT EXISTS overall_score FLOAT DEFAULT 0.0;'))
        
        await session.commit()
        logger.info("Successfully added all potentially missing columns to PostgreSQL tables.")

if __name__ == "__main__":
    asyncio.run(migrate_all())
