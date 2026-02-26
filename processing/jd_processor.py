# Job description processor

from domain.job_models import JobRequirements


def extract_requirements(jd_text: str) -> JobRequirements:
    return JobRequirements(text=jd_text.strip())