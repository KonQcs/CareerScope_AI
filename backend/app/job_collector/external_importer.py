from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.init_db import sync_sqlite_schema
from backend.app.job_collector.base import JobProvider
from backend.app.job_collector.sample_loader import (
    classify_job_posting_data,
    extract_skills_for_job,
)
from backend.app.models.job import JobPosting, JobSkill
from backend.app.services.data_quality import validate_job_posting, validate_job_skill


def import_jobs_from_provider(
    session: Session,
    provider: JobProvider,
    query: str,
    location: str | None = None,
    country: str | None = None,
    page: int = 1,
) -> dict[str, Any]:
    sync_sqlite_schema(session.get_bind())
    fetched_jobs = provider.search_jobs(
        query=query,
        location=location,
        country=country,
        page=page,
    )

    inserted_count = 0
    skipped_duplicates = 0
    validation_issues: list[dict[str, Any]] = []

    for raw_job in fetched_jobs:
        job_data = classify_job_posting_data(_ensure_external_id(raw_job, provider.provider_name))
        external_id = str(job_data["external_id"])

        existing_job = session.scalar(
            select(JobPosting).where(JobPosting.external_id == external_id)
        )
        if existing_job is not None:
            skipped_duplicates += 1
            continue

        job_issues = validate_job_posting(job_data)
        if job_issues:
            validation_issues.append({"external_id": external_id, "issues": job_issues})
            continue

        job = _job_posting_from_dict(job_data)
        session.add(job)
        session.flush()

        for skill_data in extract_skills_for_job(job_data):
            skill_issues = validate_job_skill(skill_data)
            if skill_issues:
                validation_issues.append(
                    {
                        "external_id": external_id,
                        "skill": skill_data.get("normalized_skill_name"),
                        "issues": skill_issues,
                    }
                )
                continue
            session.add(JobSkill(job_id=job.id, **skill_data))

        inserted_count += 1

    session.commit()
    return {
        "provider": provider.provider_name,
        "query": query,
        "fetched_jobs": len(fetched_jobs),
        "inserted_jobs": inserted_count,
        "skipped_duplicates": skipped_duplicates,
        "validation_issues": validation_issues,
        "error": getattr(provider, "last_error", None),
    }


def _ensure_external_id(job_data: dict[str, Any], provider_name: str) -> dict[str, Any]:
    normalized_job = dict(job_data)
    if normalized_job.get("external_id"):
        return normalized_job

    stable_parts = [
        provider_name,
        str(normalized_job.get("title") or "unknown-title"),
        str(normalized_job.get("company") or "unknown-company"),
        str(normalized_job.get("source_url") or ""),
    ]
    normalized_job["external_id"] = ":".join(stable_parts)
    return normalized_job


def _job_posting_from_dict(job_data: dict[str, Any]) -> JobPosting:
    return JobPosting(
        external_id=job_data["external_id"],
        title=job_data["title"],
        company=job_data["company"],
        field=job_data.get("field"),
        job_family=job_data.get("job_family"),
        location=job_data.get("location"),
        country=job_data.get("country"),
        remote_type=job_data.get("remote_type"),
        seniority=job_data.get("seniority"),
        salary_min=job_data.get("salary_min"),
        salary_max=job_data.get("salary_max"),
        description=job_data.get("description"),
        requirements_text=job_data.get("requirements_text"),
        source=job_data.get("source"),
        source_url=job_data.get("source_url"),
        date_posted=_parse_date(job_data.get("date_posted")),
    )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)
