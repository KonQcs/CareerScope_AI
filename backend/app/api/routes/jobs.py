from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.session import get_db
from backend.app.job_collector.sample_loader import import_sample_jobs_to_db
from backend.app.models.job import JobPosting
from backend.app.schemas.job import JobPostingRead

router = APIRouter(prefix="/jobs", tags=["jobs"])

FIELD_SEARCH_TERMS = {
    "Computer Science": ("data", "engineer", "scientist", "developer", "machine learning", "ml"),
    "Finance": ("financial", "finance", "accounting", "portfolio", "valuation"),
    "Logistics": ("supply chain", "logistics", "warehouse", "inventory", "route"),
}


@router.get("", response_model=list[JobPostingRead])
def list_jobs(
    field: str | None = Query(default=None),
    title: str | None = Query(default=None),
    location: str | None = Query(default=None),
    remote_type: str | None = Query(default=None),
    seniority: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> list[JobPosting]:
    statement = select(JobPosting).options(selectinload(JobPosting.skills))

    if title:
        statement = statement.where(JobPosting.title.ilike(f"%{title}%"))
    if location:
        statement = statement.where(JobPosting.location.ilike(f"%{location}%"))
    if remote_type:
        statement = statement.where(JobPosting.remote_type.ilike(f"%{remote_type}%"))
    if seniority:
        statement = statement.where(JobPosting.seniority.ilike(f"%{seniority}%"))
    if field:
        field_terms = FIELD_SEARCH_TERMS.get(field, (field,))
        field_conditions = [
            JobPosting.title.ilike(f"%{term}%") | JobPosting.description.ilike(f"%{term}%")
            for term in field_terms
        ]
        statement = statement.where(or_(*field_conditions))

    return list(session.scalars(statement).all())


@router.post("/import-sample")
def import_sample_jobs(session: Session = Depends(get_db)) -> dict[str, int]:
    inserted_count = import_sample_jobs_to_db(session)
    return {"inserted_jobs": inserted_count}
