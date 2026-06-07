"""Pydantic schemas for API request and response models."""

from backend.app.schemas.candidate import (
    CandidateAnalysisPreview,
    CandidateProfileCreate,
    CandidateProfileRead,
    CandidateProjectRead,
    CandidateSkillRead,
)
from backend.app.schemas.job import JobPostingCreate, JobPostingRead, JobSkillRead
from backend.app.schemas.match import JobRecommendation, MatchResultRead, SkillGapReport

__all__ = [
    "CandidateAnalysisPreview",
    "CandidateProfileCreate",
    "CandidateProfileRead",
    "CandidateProjectRead",
    "CandidateSkillRead",
    "JobPostingCreate",
    "JobPostingRead",
    "JobRecommendation",
    "JobSkillRead",
    "MatchResultRead",
    "SkillGapReport",
]
