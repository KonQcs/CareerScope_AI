"""SQLAlchemy models for CareerScope AI."""

from backend.app.models.candidate import CandidateProfile, CandidateProject, CandidateSkill
from backend.app.models.job import JobPosting, JobSkill
from backend.app.models.match import MatchResult

__all__ = [
    "CandidateProfile",
    "CandidateProject",
    "CandidateSkill",
    "JobPosting",
    "JobSkill",
    "MatchResult",
]
