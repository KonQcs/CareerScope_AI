from collections.abc import Iterable
from typing import Any

from backend.app.matching.explanations import generate_match_explanation
from backend.app.matching.scoring import (
    calculate_skill_overlap,
    read_value,
    score_domain,
    score_location,
    score_portfolio_evidence,
    score_seniority,
    split_job_skills_by_importance,
)

OVERALL_WEIGHTS = {
    "required_skill_score": 0.40,
    "preferred_skill_score": 0.20,
    "seniority_score": 0.15,
    "domain_score": 0.10,
    "portfolio_evidence_score": 0.10,
    "location_score": 0.05,
}


def calculate_job_match(
    candidate_profile: Any,
    candidate_skills: Iterable[Any],
    candidate_projects: Iterable[Any],
    job: Any,
    job_skills: Iterable[Any],
) -> dict[str, Any]:
    candidate_skills = list(candidate_skills)
    candidate_projects = list(candidate_projects)
    job_skills = list(job_skills)
    required_job_skills, preferred_job_skills = split_job_skills_by_importance(job_skills)

    required_overlap = calculate_skill_overlap(candidate_skills, required_job_skills)
    preferred_overlap = _calculate_preferred_overlap(
        candidate_skills,
        preferred_job_skills,
        required_overlap["score"],
    )
    matching_skills = _merge_skill_lists(
        required_overlap["matching_skills"],
        preferred_overlap["matching_skills"],
    )
    missing_skills = _merge_skill_lists(
        required_overlap["missing_skills"],
        preferred_overlap["missing_skills"],
    )
    weak_skills = _merge_skill_lists(
        required_overlap["weak_skills"],
        preferred_overlap["weak_skills"],
    )

    component_scores = {
        "required_skill_score": required_overlap["score"],
        "preferred_skill_score": preferred_overlap["score"],
        "seniority_score": score_seniority(
            read_value(candidate_profile, "seniority_preference"),
            read_value(job, "seniority"),
        ),
        "domain_score": score_domain(candidate_profile, job),
        "portfolio_evidence_score": score_portfolio_evidence(
            candidate_projects,
            matching_skills,
        ),
        "location_score": score_location(
            read_value(candidate_profile, "location_preference"),
            read_value(candidate_profile, "remote_preference"),
            job,
        ),
    }
    overall_score = _calculate_overall_score(component_scores)
    explanation = generate_match_explanation(
        candidate_profile=candidate_profile,
        job=job,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        weak_skills=weak_skills,
        component_scores=component_scores,
    )

    return {
        "overall_score": overall_score,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "weak_skills": weak_skills,
        "explanation": explanation,
        "component_scores": component_scores,
        **component_scores,
    }


def _calculate_preferred_overlap(
    candidate_skills: list[Any],
    preferred_job_skills: list[Any],
    required_skill_score: float,
) -> dict[str, Any]:
    if preferred_job_skills:
        return calculate_skill_overlap(candidate_skills, preferred_job_skills)

    return {
        "score": round(required_skill_score * 0.85, 2),
        "matching_skills": [],
        "missing_skills": [],
        "weak_skills": [],
    }


def _calculate_overall_score(component_scores: dict[str, float]) -> float:
    return round(
        sum(component_scores[name] * weight for name, weight in OVERALL_WEIGHTS.items()),
        2,
    )


def _merge_skill_lists(*skill_lists: list[str]) -> list[str]:
    merged: set[str] = set()
    for skill_list in skill_lists:
        merged.update(skill_list)
    return sorted(merged, key=str.casefold)
