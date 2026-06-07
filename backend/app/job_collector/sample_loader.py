import json
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

from backend.app.skill_extraction.taxonomy import find_skills_in_text

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

SAMPLE_JOBS_PATH = Path(__file__).resolve().parents[3] / "data" / "sample" / "sample_jobs.json"
FIELD_KEYWORDS = {
    "Finance": ("financial analyst", "finance", "accounting", "valuation"),
    "Logistics": ("supply chain", "logistics", "warehouse", "inventory"),
    "Computer Science": (
        "data engineer",
        "data scientist",
        "ml engineer",
        "machine learning",
        "backend developer",
    ),
}


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

    inserted_count = 0

    for job_data in load_sample_jobs():
        external_id = job_data["external_id"]
        existing_job = session.scalar(
            select(JobPosting).where(JobPosting.external_id == external_id)
        )
        if existing_job is not None:
            continue

        job = _job_posting_from_dict(job_data, JobPosting)
        session.add(job)
        session.flush()

        for skill_data in extract_skills_for_job(job_data):
            session.add(JobSkill(job_id=job.id, **skill_data))

        inserted_count += 1

    session.commit()
    return inserted_count


def _job_posting_from_dict(job_data: dict[str, Any], job_model: type[Any]) -> Any:
    return job_model(
        external_id=job_data["external_id"],
        title=job_data["title"],
        company=job_data["company"],
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


def _infer_target_field(job: dict[str, Any]) -> str | None:
    title = str(job.get("title", "") or "").casefold()
    title_field = _field_from_text(title)
    if title_field is not None:
        return title_field

    haystack = " ".join(
        str(job.get(key, "") or "") for key in ("description", "requirements_text")
    ).casefold()
    return _field_from_text(haystack)


def _field_from_text(text: str) -> str | None:
    for field, keywords in FIELD_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return field
    return None


def _infer_importance(evidence_text: str) -> str:
    lowered_text = evidence_text.casefold()
    if "preferred" in lowered_text or "nice to have" in lowered_text:
        return "preferred"
    return "required"
