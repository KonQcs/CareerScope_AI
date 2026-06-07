from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.session import get_db
from backend.app.matching.service import calculate_job_match
from backend.app.matching.skill_gap import find_relevant_jobs, generate_skill_gap_report
from backend.app.models.candidate import CandidateProfile
from backend.app.models.job import JobPosting
from backend.app.schemas.match import (
    JobRecommendation,
    JobRecommendationRequest,
    SkillGapReport,
    SkillGapRequest,
)
from backend.app.skill_extraction.taxonomy import find_skills_in_text

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/{candidate_id}/skill-gap", response_model=SkillGapReport)
def create_skill_gap_report(
    candidate_id: int,
    request: SkillGapRequest,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    candidate = _get_candidate(session, candidate_id)
    jobs = _load_jobs(session)

    return generate_skill_gap_report(
        target_field=request.target_field,
        target_job_title=request.target_job_title,
        candidate_skills=candidate.skills,
        candidate_projects=candidate.projects,
        job_postings=jobs,
    )


@router.post("/{candidate_id}/recommend-jobs", response_model=list[JobRecommendation])
def recommend_jobs(
    candidate_id: int,
    request: JobRecommendationRequest,
    session: Session = Depends(get_db),
) -> list[JobRecommendation]:
    candidate = _get_candidate(session, candidate_id)
    jobs = _load_jobs(session)
    relevant_jobs = find_relevant_jobs(request.target_field, request.target_job_title, jobs)
    jobs_to_score = relevant_jobs or jobs
    candidate_profile = {
        "target_field": request.target_field,
        "target_job_title": request.target_job_title,
        "seniority_preference": candidate.seniority_preference,
        "location_preference": candidate.location_preference,
        "remote_preference": candidate.remote_preference,
    }

    recommendations: list[JobRecommendation] = []
    for job in jobs_to_score:
        match_result = calculate_job_match(
            candidate_profile=candidate_profile,
            candidate_skills=candidate.skills,
            candidate_projects=candidate.projects,
            job=job,
            job_skills=_job_skills_for_matching(job, request.target_field),
        )
        recommendations.append(
            JobRecommendation(
                job_id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                overall_score=match_result["overall_score"],
                match_label=_match_label(match_result["overall_score"]),
                matching_skills=match_result["matching_skills"],
                missing_skills=match_result["missing_skills"],
                weak_skills=match_result["weak_skills"],
                explanation=match_result["explanation"],
            )
        )

    return sorted(recommendations, key=lambda item: item.overall_score, reverse=True)[
        : request.limit
    ]


def _get_candidate(session: Session, candidate_id: int) -> CandidateProfile:
    candidate = session.scalar(
        select(CandidateProfile)
        .options(
            selectinload(CandidateProfile.skills),
            selectinload(CandidateProfile.projects),
        )
        .where(CandidateProfile.id == candidate_id)
    )
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} was not found.",
        )
    return candidate


def _load_jobs(session: Session) -> list[JobPosting]:
    return list(session.scalars(select(JobPosting).options(selectinload(JobPosting.skills))).all())


def _job_skills_for_matching(job: JobPosting, target_field: str) -> list[object]:
    if job.skills:
        return list(job.skills)

    searchable_text = " ".join(
        value or "" for value in (job.title, job.description, job.requirements_text)
    )
    return find_skills_in_text(searchable_text, field=target_field)


def _match_label(score: float) -> str:
    if score >= 80:
        return "strong"
    if score >= 60:
        return "partial"
    return "low"
