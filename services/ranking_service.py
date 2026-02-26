# Stage2 ranking logic - Business logic

import logging
import json
from typing import List, Optional, Dict
from llm.factory import get_llm_provider
from database.repositories.score_repo import update_candidate_rank

logger = logging.getLogger(__name__)

async def run_stage2_ranking(
    analysis_id: str,
    jd_text: str,
    candidates: List[dict],
    model: Optional[str] = None
):
    """
    Orchestrates Stage 2 ranking using comparative LLM analysis.
    Assumes candidates are already pre-filtered/sorted.
    """
    if not candidates:
        return

    logger.info(f"Stage 2 ranking {len(candidates)} candidates for analysis {analysis_id}")

    summaries = _build_candidate_summaries(candidates)
    prompt = _build_ranking_prompt(jd_text, summaries, len(candidates))
    
    provider = get_llm_provider(model)
    result = await provider.chat(prompt)
    
    if not result or "ranking" not in result:
        logger.error(f"LLM ranking failed or returned invalid format for analysis {analysis_id}")
        return

    ranking = result.get("ranking", [])

    for item in ranking:
        await update_candidate_rank(
            analysis_id=analysis_id,
            candidate_name=item["name"],
            rank=item["rank"],
            justification=item["justification"]
        )

def _build_candidate_summaries(candidates: List[Dict]) -> str:
    """
    Build compact candidate summaries for the ranking prompt.
    """
    lines = []
    for i, c in enumerate(candidates):
        # Check both top-level and structured_json for robustness
        struct = c.get('structured_json', {})
        
        skills = c.get('skills_text') or struct.get('skills_text')
        if not skills:
            skills_list = struct.get('skills', [])
            skills = ", ".join(skills_list) if isinstance(skills_list, list) else str(skills_list)
            
        experience = c.get('experience_text') or struct.get('experience_text') or "N/A"
        summary = c.get('summary') or struct.get('summary') or "N/A"
        
        # Breakdown values are already floats in our system (0.0 to 1.0)
        bd = c.get('breakdown', {})
        skill_score = round(float(bd.get('skill_match', 0)) * 100, 1)
        exp_score = round(float(bd.get('exp_match', 0)) * 100, 1)

        lines.append(
            f"[{i+1}] {c.get('name', 'Unknown')} | "
            f"Skills: {skill_score}% | Exp: {exp_score}%\n"
            f"    Skills-Preview: {str(skills)[:200]}...\n"
            f"    Exp-Preview: {str(experience)[:200]}...\n"
            f"    Summary: {str(summary)[:300]}"
        )
    
    summaries_text = "\n\n".join(lines)
    logger.debug(f"Stage 2 summaries built: {len(summaries_text)} chars")
    return summaries_text

def _build_ranking_prompt(jd_text: str, summaries: str, n: int) -> str:
    """
    Build the prompt for the LLM to rank candidates.
    """
    return f"""You are a senior HR expert specialising in AI/ML hiring with 10+ years experience.

Rank the {n} candidates below from 1 to {n} based on alignment with the job description.

Ranking criteria (in order of priority):
1. Skills match — required and preferred technical/soft skills
2. Experience match — relevance, depth, years, roles, achievements
3. Qualifications — education, certifications, credentials
4. Negative flags — employment gaps, missing critical skills (lower the rank)

Rules:
- No ties unless candidates are genuinely equivalent
- Missing a critical JD requirement must lower the rank unless offset by exceptional strengths elsewhere
- Be consistent across all candidates

IMPORTANT — For each candidate's justification, write `3-4` detailed sentences covering:
  a) Key matching skills and technologies
  b) Relevant experience highlights and years
  c) Any gaps or missing requirements from the JD
  d) Overall fit assessment (Strong Fit / Good Fit / Moderate Fit)

Job Description:
{jd_text}

Candidates:
{summaries}

Return ONLY valid JSON in this exact format:
{{"ranking": [{{"rank": 1, "name": "Full Name", "justification": "3-4 detailed sentences about why this candidate is ranked here, covering skills match, experience relevance, gaps, and overall fit."}}]}}"""

def calculate_stage2_count(total_candidates: int) -> int:
    """
    Calculate number of candidates to send to Stage 2 ranking.
    Formula: 75% of total, min 2, max 10.
    """
    return max(2, min(10, round(0.75 * total_candidates)))