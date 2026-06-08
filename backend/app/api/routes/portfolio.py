from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.candidate import CandidateProfile, CandidateProject, CandidateSkill
from backend.app.portfolio_analyzer import (
    PortfolioProject,
    analyze_portfolio_url,
    normalize_portfolio_links,
)
from backend.app.services.data_quality import (
    normalize_evidence_source,
    validate_candidate_skill,
)
from backend.app.skill_extraction.taxonomy import get_skill_category

router = APIRouter(prefix="/candidates", tags=["portfolio"])


class PortfolioLinksRequest(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=20)


@router.post("/{candidate_id}/portfolio")
def analyze_candidate_portfolio(
    candidate_id: int,
    request: PortfolioLinksRequest,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    candidate = session.get(CandidateProfile, candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} was not found.",
        )

    urls = normalize_portfolio_links(request.urls)
    projects: list[dict[str, object]] = []

    for url in urls:
        analyzed_projects = analyze_portfolio_url(url, target_field=candidate.target_field)
        for analyzed_project in analyzed_projects:
            project = CandidateProject(
                candidate_id=candidate.id,
                project_name=analyzed_project.name,
                source_url=analyzed_project.url,
                description=analyzed_project.description,
                detected_skills=analyzed_project.detected_skills,
                evidence_strength=analyzed_project.evidence_strength,
            )
            session.add(project)

            for skill_name in analyzed_project.detected_skills:
                evidence_source = normalize_evidence_source(analyzed_project.source)
                skill_record = {
                    "candidate_id": candidate.id,
                    "skill_name": skill_name,
                    "normalized_skill_name": skill_name,
                    "category": get_skill_category(skill_name),
                    "evidence_source": evidence_source,
                    "evidence_text": analyzed_project.evidence_text or analyzed_project.url,
                    "evidence_strength": analyzed_project.evidence_strength,
                }
                quality_issues = validate_candidate_skill(skill_record)
                if quality_issues:
                    raise HTTPException(
                        status_code=422,
                        detail=quality_issues,
                    )
                if not _candidate_has_portfolio_skill(session, candidate.id, skill_name):
                    session.add(CandidateSkill(**skill_record))

            projects.append(_project_response(analyzed_project))

    session.commit()
    return {"candidate_id": candidate.id, "projects": projects}


def _candidate_has_portfolio_skill(
    session: Session,
    candidate_id: int,
    skill_name: str,
) -> bool:
    existing_skill = session.scalar(
        select(CandidateSkill).where(
            CandidateSkill.candidate_id == candidate_id,
            CandidateSkill.normalized_skill_name == skill_name,
            CandidateSkill.evidence_source.in_(
                ("portfolio", "github", "website", "Portfolio", "GitHub")
            ),
        )
    )
    return existing_skill is not None


def _project_response(project: PortfolioProject) -> dict[str, object]:
    return {
        "project_name": project.name,
        "source_url": project.url,
        "source": project.source,
        "description": project.description,
        "detected_skills": project.detected_skills,
        "evidence_text": project.evidence_text,
        "evidence_strength": project.evidence_strength,
        "language": project.language,
        "topics": project.topics,
        "stars": project.stars,
        "forks": project.forks,
        "updated_at": project.updated_at,
    }
