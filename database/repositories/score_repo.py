# database/repositories/score_repo.py

import uuid
from sqlalchemy import select, update
from database.engine import get_db_session
from database.models import Candidate, ScoreBreakdown


async def update_candidate_scores(candidate_id: str, scores: dict):

    async with get_db_session() as session:

        result = await session.execute(
            select(ScoreBreakdown).where(
                ScoreBreakdown.candidate_id == candidate_id
            )
        )

        sb = result.scalars().first()

        if not sb:
            sb = ScoreBreakdown(candidate_id=candidate_id)
            session.add(sb)

        # Update fields
        if "skill_match" in scores: sb.skill_match = scores["skill_match"]
        if "exp_match" in scores: sb.exp_match = scores["exp_match"]
        if "education_match" in scores: sb.education_match = scores["education_match"]
        if "overall_score" in scores: sb.overall_score = scores["overall_score"]

        await session.commit()


async def update_candidate_rank(
    analysis_id: str,
    candidate_name: str,
    rank: int,
    justification: str
):

    async with get_db_session() as session:
        # 1. Find the candidate ID for the given name in this analysis
        # Note: This assumes names are unique within an analysis or handles the first one.
        result = await session.execute(
            select(Candidate.candidate_id)
            .where(Candidate.analysis_id == analysis_id)
            .where(Candidate.structured_json.op("->>")("name") == candidate_name)
        )
        candidate_id = result.scalar()

        if not candidate_id:
            return

        # 2. Upsert the rank into ScoreBreakdown
        result = await session.execute(
            select(ScoreBreakdown).where(
                ScoreBreakdown.candidate_id == candidate_id
            )
        )
        sb = result.scalars().first()

        if not sb:
            sb = ScoreBreakdown(
                candidate_id=candidate_id,
                rank=rank,
                justification=justification
            )
            session.add(sb)
        else:
            sb.rank = rank
            sb.justification = justification

        await session.commit()