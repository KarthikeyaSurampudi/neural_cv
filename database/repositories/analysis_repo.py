# Analysis repository - DB access layer

# database/repositories/analysis_repo.py

import uuid
from typing import List, Optional, Dict
from sqlalchemy import select, delete, update
from database.engine import AsyncSessionLocal
from database.models import Analysis, Candidate


async def create_analysis(
    analysis_name: str,
    jd_text: str,
    user_id: str,
    jd_hash: str,
    resume_set_hash: str,
    jd_file_path: Optional[str] = None,
    resume_files_info: Optional[Dict] = None,
):
    analysis_id = uuid.uuid4().hex
    async with AsyncSessionLocal() as session:

        analysis = Analysis(
            analysis_id=analysis_id,
            analysis_name=analysis_name,
            jd_text=jd_text,
            user_id=user_id,
            job_description_hash=jd_hash,
            resume_set_hash=resume_set_hash,
            jd_file_path=jd_file_path,
            resume_files_info=resume_files_info,
            status="pending",
            stage2_count=0
        )

        session.add(analysis)
        await session.commit()

        return analysis_id


async def get_analyses_by_user(user_id: str) -> List[Dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Analysis).where(Analysis.user_id == user_id)
        )
        analyses = result.scalars().all()
        return [
            {
                "analysis_id": a.analysis_id,
                "analysis_name": a.analysis_name,
                "status": a.status,
                "created_at": a.created_at
            }
            for a in analyses
        ]


async def delete_analysis(analysis_id: str):

    async with AsyncSessionLocal() as session:

        await session.execute(
            delete(Candidate)
            .where(Candidate.analysis_id == analysis_id)
        )

        # Then delete analysis
        await session.execute(
            delete(Analysis)
            .where(Analysis.analysis_id == analysis_id)
        )

        await session.commit()


async def find_existing_analysis(user_id: str, jd_hash: str, resume_set_hash: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .where(Analysis.job_description_hash == jd_hash)
            .where(Analysis.resume_set_hash == resume_set_hash)
        )
        return result.scalars().first()


async def update_analysis_status(analysis_id: str, status: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Analysis)
            .where(Analysis.analysis_id == analysis_id)
            .values(status=status)
        )
        await session.commit()