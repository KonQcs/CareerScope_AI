"""Role and job matching package."""
"""Candidate-to-job matching package."""

from backend.app.matching.explanations import generate_match_explanation
from backend.app.matching.scoring import (
    calculate_skill_overlap,
    score_location,
    score_seniority,
)
from backend.app.matching.service import calculate_job_match

__all__ = [
    "calculate_job_match",
    "calculate_skill_overlap",
    "generate_match_explanation",
    "score_location",
    "score_seniority",
]
