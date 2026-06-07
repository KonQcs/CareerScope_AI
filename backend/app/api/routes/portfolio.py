from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.candidate import CandidateProfile, CandidateProject, CandidateSkill
from backend.app.portfolio_analyzer.analyzer import normalize_portfolio_links
from backend.app.skill_extraction.taxonomy import find_skills_in_text

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
        project_data = _analyze_portfolio_url(url, candidate.target_field)
        project = CandidateProject(
            candidate_id=candidate.id,
            project_name=project_data["project_name"],
            source_url=url,
            description=project_data["description"],
            detected_skills=project_data["detected_skills"],
            evidence_strength=project_data["evidence_strength"],
        )
        session.add(project)

        for skill_name in project_data["detected_skills"]:
            if not _candidate_has_portfolio_skill(session, candidate.id, skill_name):
                session.add(
                    CandidateSkill(
                        candidate_id=candidate.id,
                        skill_name=skill_name,
                        normalized_skill_name=skill_name,
                        category=None,
                        evidence_source="portfolio",
                        evidence_text=url,
                        evidence_strength=0.75,
                    )
                )

        projects.append(project_data)

    session.commit()
    return {"candidate_id": candidate.id, "projects": projects}


def _analyze_portfolio_url(url: str, target_field: str) -> dict[str, object]:
    parsed_url = urlparse(url)
    host = parsed_url.netloc or parsed_url.path
    path = parsed_url.path.strip("/")
    display_name = path.split("/")[-1] if path else host
    project_name = display_name.replace("-", " ").replace("_", " ").title() or host
    searchable_text = f"{host} {path}".replace("/", " ")
    detected_skills = [skill["normalized_skill"] for skill in find_skills_in_text(searchable_text)]

    if "github" in host.casefold() and "Git" not in detected_skills:
        detected_skills.append("Git")
    if "kaggle" in host.casefold() and target_field == "Computer Science":
        for skill in ("Python", "statistics"):
            if skill not in detected_skills:
                detected_skills.append(skill)

    return {
        "project_name": project_name,
        "source_url": url,
        "description": f"Portfolio evidence from {host}.",
        "detected_skills": detected_skills,
        "evidence_strength": 0.7 if detected_skills else 0.4,
    }


def _candidate_has_portfolio_skill(
    session: Session,
    candidate_id: int,
    skill_name: str,
) -> bool:
    existing_skill = session.scalar(
        select(CandidateSkill).where(
            CandidateSkill.candidate_id == candidate_id,
            CandidateSkill.normalized_skill_name == skill_name,
            CandidateSkill.evidence_source == "portfolio",
        )
    )
    return existing_skill is not None
