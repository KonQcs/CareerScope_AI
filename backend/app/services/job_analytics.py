from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.job_collector.classification import classify_job_field
from backend.app.models.job import JobPosting, JobSkill
from backend.app.services.data_quality import normalize_job_remote_type, normalize_job_seniority

DEFAULT_LIMIT = 20


def get_jobs_by_field(session: Session) -> list[dict[str, int | str]]:
    counter: Counter[str] = Counter(_job_field(job) for job in _load_jobs(session))
    return _counter_to_rows(counter, "field")


def get_jobs_by_seniority(session: Session) -> list[dict[str, int | str]]:
    counter: Counter[str] = Counter(
        normalize_job_seniority(job.seniority) or "Unknown" for job in _load_jobs(session)
    )
    return _counter_to_rows(counter, "seniority")


def get_jobs_by_remote_type(session: Session) -> list[dict[str, int | str]]:
    counter: Counter[str] = Counter(
        normalize_job_remote_type(job.remote_type) or "Unknown" for job in _load_jobs(session)
    )
    return _counter_to_rows(counter, "remote_type")


def get_top_skills(session: Session, limit: int = DEFAULT_LIMIT) -> list[dict[str, int | str]]:
    counter: Counter[str] = Counter()
    categories: dict[str, str | None] = {}

    for skill in _load_job_skills(session):
        skill_name = _skill_name(skill)
        if not skill_name:
            continue
        counter[skill_name] += 1
        categories.setdefault(skill_name, skill.category)

    return _skill_counter_to_rows(counter, categories, limit)


def get_top_skills_by_field(
    session: Session,
    field: str,
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, int | str]]:
    counter: Counter[str] = Counter()
    categories: dict[str, str | None] = {}

    for job in _load_jobs(session):
        if _job_field(job).casefold() != field.casefold():
            continue
        for skill in job.skills:
            skill_name = _skill_name(skill)
            if not skill_name:
                continue
            counter[skill_name] += 1
            categories.setdefault(skill_name, skill.category)

    return _skill_counter_to_rows(counter, categories, limit)


def get_top_companies(session: Session, limit: int = 10) -> list[dict[str, int | str]]:
    counter: Counter[str] = Counter(
        job.company.strip() for job in _load_jobs(session) if job.company and job.company.strip()
    )
    return _counter_to_rows(counter, "company", limit=limit)


def get_salary_summary(session: Session) -> list[dict[str, float | int | str | None]]:
    grouped_jobs: dict[str, list[JobPosting]] = defaultdict(list)
    salary_jobs = [
        job
        for job in _load_jobs(session)
        if job.salary_min is not None or job.salary_max is not None
    ]

    for job in salary_jobs:
        grouped_jobs[_job_field(job)].append(job)

    rows = [_salary_row("Overall", salary_jobs)]
    rows.extend(_salary_row(field, jobs) for field, jobs in sorted(grouped_jobs.items()))
    return [row for row in rows if row["job_count"] > 0]


def build_job_analytics_payload(
    session: Session,
    target_field: str | None = None,
) -> dict[str, Any]:
    field = target_field or "Computer Science"
    return {
        "jobs_by_field": get_jobs_by_field(session),
        "jobs_by_seniority": get_jobs_by_seniority(session),
        "jobs_by_remote_type": get_jobs_by_remote_type(session),
        "top_skills_overall": get_top_skills(session),
        "top_skills_by_target_field": get_top_skills_by_field(session, field),
        "target_field": field,
        "top_companies": get_top_companies(session),
        "salary_summary": get_salary_summary(session),
    }


def _load_jobs(session: Session) -> list[JobPosting]:
    return list(session.scalars(select(JobPosting).options(selectinload(JobPosting.skills))).all())


def _load_job_skills(session: Session) -> list[JobSkill]:
    return list(session.scalars(select(JobSkill)).all())


def _job_field(job: JobPosting) -> str:
    if job.field and job.field.strip():
        return job.field.strip()

    description = " ".join(part or "" for part in (job.description, job.requirements_text))
    return classify_job_field(job.title or "", description)


def _skill_name(skill: JobSkill) -> str:
    return (skill.normalized_skill_name or skill.skill_name or "").strip()


def _counter_to_rows(
    counter: Counter[str],
    label_key: str,
    limit: int | None = None,
) -> list[dict[str, int | str]]:
    rows = [
        {label_key: label, "count": count} for label, count in counter.most_common(limit) if label
    ]
    return sorted(rows, key=lambda row: (-int(row["count"]), str(row[label_key]).casefold()))


def _skill_counter_to_rows(
    counter: Counter[str],
    categories: dict[str, str | None],
    limit: int,
) -> list[dict[str, int | str]]:
    rows = []
    for skill, count in counter.most_common(limit):
        rows.append(
            {
                "skill": skill,
                "category": categories.get(skill) or "unknown",
                "count": count,
            }
        )
    return rows


def _salary_row(field: str, jobs: list[JobPosting]) -> dict[str, float | int | str | None]:
    salary_mins = [float(job.salary_min) for job in jobs if job.salary_min is not None]
    salary_maxes = [float(job.salary_max) for job in jobs if job.salary_max is not None]

    return {
        "field": field,
        "job_count": len(jobs),
        "salary_min": min(salary_mins) if salary_mins else None,
        "salary_max": max(salary_maxes) if salary_maxes else None,
        "average_salary_min": round(mean(salary_mins), 2) if salary_mins else None,
        "average_salary_max": round(mean(salary_maxes), 2) if salary_maxes else None,
    }
