# domain/__init__.py

from .resume_models import ResumeData
from .job_models import JobRequirements
from .ranking_models import RankedCandidate, RankingResponse

__all__ = [
    "ResumeData",
    "JobRequirements",
    "RankedCandidate",
    "RankingResponse",
]