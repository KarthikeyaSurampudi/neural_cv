# SQLAlchemy models

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
    Float,
    Integer
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "user"

    user_id = Column(String(32), primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    
    # Security fields
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    must_change_password = Column(Boolean, default=False)


class Analysis(Base, TimestampMixin):
    __tablename__ = "analysis"

    analysis_id = Column(String(32), primary_key=True)
    analysis_name = Column(String(255), nullable=False)
    job_description_hash = Column(String(64), nullable=False)
    jd_text = Column(Text, nullable=False)
    jd_file_path = Column(String(500), nullable=True)
    
    resume_files_info = Column(JSON, nullable=True)
    resume_set_hash = Column(String(64), nullable=True)
    status = Column(String(50), default="pending")
    stage2_count = Column(Integer, default=0)

    user_id = Column(String(32), ForeignKey("user.user_id"), nullable=True)


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidate"

    candidate_id = Column(String(32), primary_key=True)
    analysis_id = Column(String(32), ForeignKey("analysis.analysis_id"), nullable=False)

    raw_text = Column(Text, nullable=False)
    structured_json = Column(JSON, nullable=False)
    
    summary = Column(Text, nullable=True)
    resume_hash = Column(String(64), nullable=True)
    filename = Column(String(500), nullable=True)
    
    skills_text = Column(Text, nullable=True)
    experience_text = Column(Text, nullable=True)
    was_cached = Column(Boolean, default=False)


class ScoreBreakdown(Base, TimestampMixin):
    __tablename__ = "score_breakdown"

    candidate_id = Column(String(32), ForeignKey("candidate.candidate_id"), primary_key=True)
    
    skill_match = Column(Float, default=0.0)
    exp_match = Column(Float, default=0.0)
    education_match = Column(Float, default=0.0)
    
    overall_score = Column(Float, default=0.0)
    rank = Column(Integer, nullable=True)
    justification = Column(Text, nullable=True)