"""Candidate-to-job matching package."""

from backend.app.matching.explanations import generate_match_explanation
from backend.app.matching.scoring import (
    calculate_skill_overlap,
    score_location,
    score_seniority,
)
from backend.app.matching.service import calculate_job_match
from backend.app.matching.skill_gap import generate_skill_gap_report

__all__ = [
    "calculate_job_match",
    "calculate_skill_overlap",
    "generate_skill_gap_report",
    "generate_match_explanation",
    "score_location",
    "score_seniority",
]
