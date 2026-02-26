# domain/resume_models.py

from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class ExperienceItem(BaseModel):
    role: Optional[str] = None
    years: Optional[float] = 0.0
    company: Optional[str] = None


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None


class ResumeData(BaseModel):
    # Identity
    name: Optional[str] = "Unknown"
    email: Optional[str] = None
    phone: Optional[str] = None

    # Skills & Experience
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)

    # Computed Experience
    total_experience: Optional[float] = 0.0
    relevant_experience: Optional[float] = 0.0

    # LLM Summary & Detailed Text
    summary: Optional[str] = None
    skills_text: Optional[str] = None
    experience_text: Optional[str] = None

    # Stage 1 & 2 Scores (Matching ScoreBreakdown)
    skill_match: Optional[float] = Field(0.0, validation_alias="skills_match")
    exp_match: Optional[float] = Field(0.0, validation_alias="experience_match")
    education_match: Optional[float] = Field(0.0, validation_alias="edu_match")
    overall_score: Optional[float] = Field(0.0, validation_alias="total_score")

    # Metadata
    filename: Optional[str] = None
    resume_hash: Optional[str] = None
    raw_text: Optional[str] = None

    # Stage 2 Ranking
    rank: Optional[int] = None
    justification: Optional[str] = None