# Resume parsing + stage1 scoring - Business logic

from pathlib import Path
from typing import Optional, Dict, Any
import json
import logging

from processing.resume_text_extractor import extract_text
from processing.resume_preprocessor import preprocess_resume_text
from llm.factory import get_llm_provider
from domain.resume_models import ResumeData

logger = logging.getLogger(__name__)

def flatten_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """Flattens nested dictionaries in LLM output for flat fields."""
    output = data.copy()
    
    # Expected flat string fields
    str_fields = ["summary", "skills_text", "experience_text", "name", "email", "phone"]
    # Expected float fields (Scores should be 0.0 - 1.0)
    float_fields = ["skill_match", "exp_match", "education_match", "overall_score"]
    # Other numeric fields
    other_num_fields = ["total_experience", "relevant_experience"]
    
    for field in str_fields:
        if field in output and isinstance(output[field], dict):
            output[field] = " ".join(str(v) for v in output[field].values())
            
    for field in float_fields + other_num_fields:
        if field in output:
            val = output[field]
            if isinstance(val, dict):
                nums = [v for v in val.values() if isinstance(v, (int, float))]
                val = nums[0] if nums else 0.0
            elif isinstance(val, str):
                # Handle "80%" or "0.85"
                clean_val = val.replace("%", "").strip()
                try:
                    val = float(clean_val)
                except ValueError:
                    val = 0.0
            
            # Normalize scores to 0.0-1.0
            if field in float_fields:
                if val > 1.0:
                    val = val / 100.0
                val = max(0.0, min(1.0, val))
            
            output[field] = val
                    
    return output

async def parse_and_score_resume(
    path: Path,
    jd_text: str,
    model: Optional[str] = None
) -> ResumeData:

    raw_text = extract_text(path)
    
    # Preprocess both to clean white space and stay within limits
    cleaned_resume = preprocess_resume_text(raw_text)
    cleaned_jd = preprocess_resume_text(jd_text, max_chars=3000)

    logger.info(f"Processing candidate: {path.name}")
    logger.debug(f"Cleaned Resume Length: {len(cleaned_resume)}")
    logger.debug(f"Cleaned JD Length: {len(cleaned_jd)}")

    if not cleaned_resume.strip() or len(cleaned_resume) < 50:
        logger.warning(f"Extracted text for {path.name} is too short or empty. Length: {len(cleaned_resume)}")
        return ResumeData(
            filename=path.name, 
            raw_text=raw_text,
            summary="[PARSING FAILED: EXTRACTED TEXT IS EMPTY OR TOO SHORT]"
        )

    provider = get_llm_provider(model)
    schema_definition = ResumeData.model_json_schema()

    prompt = f"""
You are an expert HR Data Scientist. Your goal is to extract information from a resume and match it against a Job Description.

MATCHING CRITERIA:
- skill_match (0.0 - 1.0): How well do the candidate's technical and soft skills align with the JD requirements?
- exp_match (0.0 - 1.0): Does the candidate have the required years of experience and relevant industry/role depth?
- education_match (0.0 - 1.0): Does the candidate meet the degree or certification requirements?
- overall_score (0.0 - 1.0): A weighted average of the above based on JD priority.

STRICT RULES:
1. Return ONLY valid JSON matching this schema: {json.dumps(schema_definition)}
2. If some information is missing, infer values based on context. 
3. Scores MUST be floats between 0.0 and 1.0. (e.g., 0.85, 0.45, 0.0). NEVER return 0.0 unless there is absolutely no match.
4. Do NOT include any conversation or markdown.

JOB DESCRIPTION:
{cleaned_jd}

---
RESUME:
{cleaned_resume}
"""

    # ---------------- FIRST ATTEMPT ----------------
    try:
        result = await provider.chat(prompt)
    except Exception as e:
        logger.warning(f"LLM Chat Call failed for {path.name}: {e}")
        result = {}

    # Diagnostic Dump
    try:
        debug_path = Path("logs/debug_llm.txt")
        debug_path.parent.mkdir(exist_ok=True)
        with open(debug_path, "a", encoding="utf-8") as dbg:
            dbg.write(f"\n{'='*50}\nFILE: {path.name}\nPROMPT:\n{prompt[:500]}...\nRESPONSE:\n{str(result)[:1000]}\n")
    except: pass

    try:
        # Sometimes LLMs return a string for JSON
        if isinstance(result, str):
            result = result.strip()
            # Remove possible markdown markers
            if result.startswith("```json"):
                result = result[7:-3].strip()
            elif result.startswith("```"):
                result = result[3:-3].strip()
            
            try:
                result = json.loads(result)
            except:
                import re
                match = re.search(r"\{.*\}", result, re.DOTALL)
                if match: result = json.loads(match.group())

        cleaned_result = flatten_result(result)
        cleaned_result["raw_text"] = raw_text
        cleaned_result["filename"] = path.name
        return ResumeData.model_validate(cleaned_result)

    except Exception as e:
        logger.warning(f"Initial LLM parse failed for {path.name}: {e}. Retrying.")

        # ---------------- RETRY WITH REPAIR ----------------
        repair_prompt = f"""
Fix this JSON to match the pydantic schema. Ensure scores are numbers 0.0-1.0.
Schema: {json.dumps(schema_definition)}
Previous malformed JSON: {json.dumps(result)}
"""
        result = await provider.chat(repair_prompt)
        
        try:
            if isinstance(result, str):
                import re
                match = re.search(r"\{.*\}", result, re.DOTALL)
                if match: result = json.loads(match.group())

            cleaned_result = flatten_result(result)
            cleaned_result["raw_text"] = raw_text
            cleaned_result["filename"] = path.name
            return ResumeData.model_validate(cleaned_result)
        except Exception as final_err:
            logger.error(f"Final parse failed: {final_err}")
            # Return partial data if possible instead of crashing
            return ResumeData(filename=path.name, raw_text=raw_text, summary="[PARSING FAILED]")