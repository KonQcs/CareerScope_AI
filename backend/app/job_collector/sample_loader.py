import json
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

from backend.app.db.init_db import sync_sqlite_schema
from backend.app.job_collector.classification import (
    classify_job_family,
    classify_job_field,
    classify_seniority,
    normalize_remote_type,
)
from backend.app.services.data_quality import (
    normalize_job_remote_type,
    normalize_job_seniority,
    normalize_job_skill_importance,
    validate_job_posting,
    validate_job_skill,
)
from backend.app.skill_extraction.taxonomy import find_skills_in_text

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

SAMPLE_JOBS_PATH = Path(__file__).resolve().parents[3] / "data" / "sample" / "sample_jobs.json"


def load_sample_jobs() -> list[dict[str, Any]]:
    with SAMPLE_JOBS_PATH.open(encoding="utf-8") as jobs_file:
        jobs = json.load(jobs_file)

    if not isinstance(jobs, list):
        raise ValueError("Sample jobs file must contain a list of job postings.")
    return jobs


def extract_skills_for_job(job: dict[str, Any]) -> list[dict[str, str]]:
    searchable_text = " ".join(
        str(job.get(key, "") or "") for key in ("title", "description", "requirements_text")
    )
    target_field = _infer_target_field(job)
    matches = find_skills_in_text(searchable_text, field=target_field)

    return [
        {
            "skill_name": match["skill"],
            "normalized_skill_name": match["normalized_skill"],
            "category": match["category"],
            "importance": _infer_importance(match["evidence_snippet"]),
            "evidence_text": match["evidence_snippet"],
        }
        for match in matches
    ]


def import_sample_jobs_to_db(session: "Session") -> int:
    from sqlalchemy import select

    from backend.app.models.job import JobPosting, JobSkill

    sync_sqlite_schema(session.get_bind())
    inserted_count = 0

    for job_data in load_sample_jobs():
        job_data = classify_job_posting_data(job_data)
        external_id = job_data["external_id"]
        existing_job = session.scalar(
            select(JobPosting).where(JobPosting.external_id == external_id)
        )
        if existing_job is not None:
            continue

        job_issues = validate_job_posting(job_data)
        if job_issues:
            raise ValueError(_format_quality_errors(external_id, job_issues))

        job = _job_posting_from_dict(job_data, JobPosting)
        session.add(job)
        session.flush()

        for skill_data in extract_skills_for_job(job_data):
            skill_issues = validate_job_skill(skill_data)
            if skill_issues:
                raise ValueError(_format_quality_errors(f"{external_id}:job_skill", skill_issues))
            session.add(JobSkill(job_id=job.id, **skill_data))

        inserted_count += 1

    session.commit()
    return inserted_count


def _job_posting_from_dict(job_data: dict[str, Any], job_model: type[Any]) -> Any:
    classified_job_data = classify_job_posting_data(job_data)
    return job_model(
        external_id=classified_job_data["external_id"],
        title=classified_job_data["title"],
        company=classified_job_data["company"],
        field=classified_job_data.get("field"),
        job_family=classified_job_data.get("job_family"),
        location=classified_job_data.get("location"),
        country=classified_job_data.get("country"),
        remote_type=classified_job_data.get("remote_type"),
        seniority=classified_job_data.get("seniority"),
        salary_min=classified_job_data.get("salary_min"),
        salary_max=classified_job_data.get("salary_max"),
        description=classified_job_data.get("description"),
        requirements_text=classified_job_data.get("requirements_text"),
        source=classified_job_data.get("source"),
        source_url=classified_job_data.get("source_url"),
        date_posted=_parse_date(classified_job_data.get("date_posted")),
    )


def classify_job_posting_data(job_data: dict[str, Any]) -> dict[str, Any]:
    classified_job = dict(job_data)
    title = str(classified_job.get("title", "") or "")
    description = _classification_text(classified_job)

    if not classified_job.get("field"):
        classified_job["field"] = classify_job_field(title, description)
    if not classified_job.get("job_family"):
        classified_job["job_family"] = classify_job_family(title, description)
    if not classified_job.get("seniority"):
        classified_job["seniority"] = classify_seniority(title, description)
    classified_job["seniority"] = normalize_job_seniority(classified_job.get("seniority"))

    if not classified_job.get("remote_type"):
        classified_job["remote_type"] = normalize_remote_type(
            " ".join(
                str(classified_job.get(key, "") or "")
                for key in ("title", "location", "description", "requirements_text")
            )
        )
    classified_job["remote_type"] = normalize_job_remote_type(classified_job.get("remote_type"))

    return classified_job


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _infer_target_field(job: dict[str, Any]) -> str | None:
    classified_field = str(
        job.get("field")
        or classify_job_field(str(job.get("title", "") or ""), _classification_text(job))
    )
    return None if classified_field == "Other" else classified_field


def _infer_importance(evidence_text: str) -> str:
    lowered_text = evidence_text.casefold()
    if "preferred" in lowered_text or "nice to have" in lowered_text:
        return normalize_job_skill_importance("preferred") or "preferred"
    return normalize_job_skill_importance("required") or "required"


def _classification_text(job: dict[str, Any]) -> str:
    return " ".join(str(job.get(key, "") or "") for key in ("description", "requirements_text"))


def _format_quality_errors(entity_id: str, issues: list[str]) -> str:
    return f"Data quality issues for {entity_id}: {'; '.join(issues)}"
