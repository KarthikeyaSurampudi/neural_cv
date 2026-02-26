# Analysis service - Business logic

import asyncio
import uuid
from pathlib import Path
from typing import List, Optional, Dict

from database.repositories.analysis_repo import (
    create_analysis,
    get_analyses_by_user,
    delete_analysis,
    find_existing_analysis,
    update_analysis_status
)
from database.repositories.candidate_repo import (
    add_candidate,
    get_candidates_by_analysis
)
from database.repositories.score_repo import update_candidate_scores

from services.resume_service import parse_and_score_resume
from services.ranking_service import run_stage2_ranking


async def process_analysis(
    analysis_name: str,
    jd_text: str,
    resume_paths: List[Path],
    user_id: str,
    model: Optional[str] = None,
    force_rerun: bool = False,
    progress_callback=None
):

    from utils.hash_utils import hash_text, hash_resume_set

    jd_hash = hash_text(jd_text)
    resume_set_hash = hash_resume_set(resume_paths)

    existing = await find_existing_analysis(
        user_id,
        jd_hash,
        resume_set_hash
    )

    if existing and not force_rerun:
        return {
            "status": "cached",
            "analysis_id": existing.analysis_id
        }

    # ---------------- CREATE ANALYSIS ----------------
    analysis_id = await create_analysis(
        analysis_name=analysis_name,
        jd_text=jd_text,
        user_id=user_id,
        jd_hash=jd_hash,
        resume_set_hash=resume_set_hash
    )

    semaphore = asyncio.Semaphore(5)
    total = len(resume_paths)
    processed = {"count": 0, "cached": 0, "llm": 0}

    # ---------------- STAGE 1 ----------------
    async def process_one(path: Path):
        async with semaphore:
            from utils.hash_utils import hash_file
            
            resume_hash = hash_file(path)

            from database.repositories.candidate_repo import get_cached_candidate_data
            cached_data = await get_cached_candidate_data(resume_hash, jd_hash)

            if cached_data:
                c = cached_data["candidate"]
                sb = cached_data["breakdown"]
                
                candidate_id = await add_candidate(
                    analysis_id=analysis_id,
                    raw_text=c.raw_text,
                    structured_data=c.structured_json,
                    summary=c.summary,
                    skills_text=c.skills_text,
                    experience_text=c.experience_text,
                    was_cached=True
                )

                if sb:
                    await update_candidate_scores(
                        candidate_id=candidate_id,
                        scores={
                            "skill_match": sb.skill_match,
                            "exp_match": sb.exp_match,
                            "education_match": sb.education_match,
                            "overall_score": sb.overall_score,
                        }
                    )

                processed["count"] += 1
                processed["cached"] += 1
                if progress_callback:
                    progress_callback("stage1", processed["count"], total,
                                      f"⚡ Cache hit: {path.name}")
                return

            # CACHE MISS: Call LLM
            if progress_callback:
                progress_callback("stage1", processed["count"], total,
                                  f"🤖 LLM call: {path.name}")

            resume_data = await parse_and_score_resume(
                path=path,
                jd_text=jd_text,
                model=model
            )

            struct_data = resume_data.model_dump()
            struct_data["resume_hash"] = resume_hash
            struct_data["filename"] = path.name

            candidate_id = await add_candidate(
                analysis_id=analysis_id,
                raw_text=resume_data.raw_text,
                structured_data=struct_data,
                summary=resume_data.summary,
                skills_text=resume_data.skills_text,
                experience_text=resume_data.experience_text,
                was_cached=False
            )

            await update_candidate_scores(
                candidate_id=candidate_id,
                scores={
                    "skill_match": resume_data.skill_match,
                    "exp_match": resume_data.exp_match,
                    "education_match": resume_data.education_match,
                    "overall_score": resume_data.overall_score,
                }
            )

            processed["count"] += 1
            processed["llm"] += 1
            if progress_callback:
                progress_callback("stage1", processed["count"], total,
                                  f"✅ Done: {path.name}")

    await asyncio.gather(*(process_one(p) for p in resume_paths))

    await update_analysis_status(analysis_id, "stage1_completed")

    if progress_callback:
        progress_callback("stage2", 0, 1, "🏆 Running Stage 2 expert ranking...")

    # ---------------- STAGE 2 ----------------
    all_candidates = await get_candidates_by_analysis(analysis_id)
    
    STAGE2_THRESHOLD = 0.80
    qualified = [
        c for c in all_candidates
        if c['breakdown'].get('overall_score', 0) >= STAGE2_THRESHOLD
    ]
    top_candidates = sorted(
        qualified,
        key=lambda x: x['breakdown'].get('overall_score', 0),
        reverse=True
    )[:10]

    if top_candidates:
        await run_stage2_ranking(
            analysis_id=analysis_id,
            jd_text=jd_text,
            candidates=top_candidates,
            model=model
        )

    if progress_callback:
        progress_callback("done", 1, 1, f"✅ Complete — {processed['llm']} LLM | {processed['cached']} cached")

    await update_analysis_status(analysis_id, "completed")

    return {
        "status": "completed",
        "analysis_id": analysis_id
    }

async def get_user_analyses(user_id: str):

    analyses = await get_analyses_by_user(user_id)

    return [
        {
            "analysis_id": a["analysis_id"],
            "analysis_name": a["analysis_name"],
            "created_at": a["created_at"],
            "status": a["status"],
        }
        for a in analyses
    ]

async def delete_analysis_by_id(analysis_id: str):
    return await delete_analysis(analysis_id)