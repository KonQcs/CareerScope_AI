from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.init_db import sync_sqlite_schema
from backend.app.db.session import get_db
from backend.app.job_collector.external_importer import import_jobs_from_provider
from backend.app.job_collector.providers.adzuna_provider import AdzunaProvider
from backend.app.job_collector.sample_loader import import_sample_jobs_to_db
from backend.app.models.job import JobPosting
from backend.app.schemas.job import JobPostingRead
from backend.app.services.job_analytics import build_job_analytics_payload

router = APIRouter(prefix="/jobs", tags=["jobs"])

FIELD_SEARCH_TERMS = {
    "Computer Science": ("data", "engineer", "scientist", "developer", "machine learning", "ml"),
    "Finance": ("financial", "finance", "accounting", "portfolio", "valuation"),
    "Logistics": ("supply chain", "logistics", "warehouse", "inventory", "route"),
}


class ExternalJobSearchRequest(BaseModel):
    provider: str = Field(default="adzuna", pattern="^adzuna$")
    query: str = Field(min_length=2, max_length=160)
    location: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    page: int = Field(default=1, ge=1, le=20)


@router.get("", response_model=list[JobPostingRead])
def list_jobs(
    field: str | None = Query(default=None),
    title: str | None = Query(default=None),
    location: str | None = Query(default=None),
    remote_type: str | None = Query(default=None),
    seniority: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> list[JobPosting]:
    sync_sqlite_schema(session.get_bind())
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
        field_conditions = [JobPosting.field.ilike(f"%{field}%")]
        field_conditions.extend(
            JobPosting.title.ilike(f"%{term}%") | JobPosting.description.ilike(f"%{term}%")
            for term in field_terms
        )
        statement = statement.where(or_(*field_conditions))

    return list(session.scalars(statement).all())


@router.get("/analytics")
def get_job_analytics(
    field: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> dict[str, object]:
    sync_sqlite_schema(session.get_bind())
    return build_job_analytics_payload(session, target_field=field)


@router.post("/search-external")
def search_external_jobs(
    request: ExternalJobSearchRequest,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    provider = AdzunaProvider()
    return import_jobs_from_provider(
        session=session,
        provider=provider,
        query=request.query,
        location=request.location,
        country=request.country,
        page=request.page,
    )


@router.post("/import-sample")
def import_sample_jobs(session: Session = Depends(get_db)) -> dict[str, int]:
    inserted_count = import_sample_jobs_to_db(session)
    return {"inserted_jobs": inserted_count}
