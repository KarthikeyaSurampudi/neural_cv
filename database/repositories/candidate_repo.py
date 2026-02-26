# Candidate repository - DB access layer

# database/repositories/candidate_repo.py

import uuid
from typing import List, Dict, Optional
from sqlalchemy import select
from database.engine import AsyncSessionLocal
from database.models import Candidate


async def add_candidate(
    analysis_id: str,
    raw_text: str,
    structured_data: dict,
    summary: Optional[str] = None,
    skills_text: Optional[str] = None,
    experience_text: Optional[str] = None,
    resume_hash: Optional[str] = None,
    filename: Optional[str] = None,
    was_cached: bool = False
) -> str:
    candidate_id = uuid.uuid4().hex
    async with AsyncSessionLocal() as session:
        candidate = Candidate(
            candidate_id=candidate_id,
            analysis_id=analysis_id,
            raw_text=raw_text,
            structured_json=structured_data,
            filename=filename or structured_data.get("filename"),
            resume_hash=resume_hash or structured_data.get("resume_hash"),
            summary=summary,
            skills_text=skills_text,
            experience_text=experience_text,
            was_cached=was_cached
        )
        session.add(candidate)
        await session.commit()
        return candidate_id


async def get_candidates_by_analysis(analysis_id: str) -> List[Dict]:
    async with AsyncSessionLocal() as session:
        from database.models import Candidate, ScoreBreakdown
        
        # Joined load or separate queries - for now let's use a join to get everything
        result = await session.execute(
            select(Candidate, ScoreBreakdown)
            .outerjoin(ScoreBreakdown, Candidate.candidate_id == ScoreBreakdown.candidate_id)
            .where(Candidate.analysis_id == analysis_id)
        )
        
        rows = result.all()
        
        candidates = []
        for c, s in rows:
            candidates.append({
                "candidate_id": c.candidate_id,
                "name": c.structured_json.get("name"),
                "filename": c.filename,
                "summary": c.summary,
                "breakdown": {
                    "skill_match": s.skill_match if s else 0,
                    "exp_match": s.exp_match if s else 0,
                    "education_match": s.education_match if s else 0,
                    "overall_score": s.overall_score if s else 0,
                    "rank": s.rank if s else None,
                    "justification": s.justification if s else None
                },
                "structured_json": c.structured_json
            })
        
        return candidates

async def get_cached_candidate_data(resume_hash: str, jd_hash: str) -> Optional[Dict]:
    """Finds an existing processed candidate with same resume + same JD (any analysis)."""
    async with AsyncSessionLocal() as session:
        from database.models import Analysis, ScoreBreakdown
        
        result = await session.execute(
            select(Candidate, ScoreBreakdown)
            .join(Analysis, Candidate.analysis_id == Analysis.analysis_id)
            .outerjoin(ScoreBreakdown, Candidate.candidate_id == ScoreBreakdown.candidate_id)
            .where(Candidate.resume_hash == resume_hash)
            .where(Analysis.job_description_hash == jd_hash)
            .limit(1)
        )
        row = result.first()
        if not row:
            return None
        
        c, sb = row
        return {
            "candidate": c,
            "breakdown": sb
        }