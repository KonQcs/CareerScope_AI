from backend.app import models as _models  # noqa: F401
from backend.app.db.base import Base
from backend.app.job_collector.sample_loader import import_sample_jobs_to_db
from backend.app.services.job_analytics import (
    build_job_analytics_payload,
    get_jobs_by_field,
    get_jobs_by_remote_type,
    get_jobs_by_seniority,
    get_salary_summary,
    get_top_companies,
    get_top_skills,
    get_top_skills_by_field,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_jobs_by_field_uses_sample_classifications() -> None:
    with _sample_jobs_session() as session:
        rows = get_jobs_by_field(session)

    counts = _row_counts(rows, "field")
    assert counts["Computer Science"] == 12
    assert counts["Finance"] == 3
    assert counts["Logistics"] == 3


def test_jobs_by_seniority_and_remote_type() -> None:
    with _sample_jobs_session() as session:
        seniority_counts = _row_counts(get_jobs_by_seniority(session), "seniority")
        remote_counts = _row_counts(get_jobs_by_remote_type(session), "remote_type")

    assert seniority_counts["Junior"] > 0
    assert seniority_counts["Senior"] > 0
    assert remote_counts["Remote"] > 0
    assert remote_counts["Hybrid"] > 0


def test_top_skills_and_top_skills_by_field() -> None:
    with _sample_jobs_session() as session:
        top_skills = get_top_skills(session, limit=10)
        finance_skills = get_top_skills_by_field(session, "Finance", limit=10)

    top_skill_names = {row["skill"] for row in top_skills}
    finance_skill_names = {row["skill"] for row in finance_skills}
    assert {"Python", "SQL"} & top_skill_names
    assert {"financial modeling", "risk analysis", "Excel"} & finance_skill_names


def test_top_companies_and_salary_summary() -> None:
    with _sample_jobs_session() as session:
        companies = get_top_companies(session, limit=5)
    salary_summary = get_salary_summary(session)

    assert len(companies) == 5
    company_counts = [int(row["count"]) for row in companies]
    assert all(count > 0 for count in company_counts)
    assert company_counts == sorted(company_counts, reverse=True)
    overall = next(row for row in salary_summary if row["field"] == "Overall")
    assert overall["job_count"] == 18
    assert overall["salary_min"] is not None
    assert overall["salary_max"] is not None


def test_analytics_payload_contains_requested_sections() -> None:
    with _sample_jobs_session() as session:
        payload = build_job_analytics_payload(session, target_field="Logistics")

    assert payload["target_field"] == "Logistics"
    assert payload["jobs_by_field"]
    assert payload["jobs_by_seniority"]
    assert payload["jobs_by_remote_type"]
    assert payload["top_skills_overall"]
    assert payload["top_skills_by_target_field"]
    assert payload["top_companies"]
    assert payload["salary_summary"]


def _sample_jobs_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = Session(engine)
    import_sample_jobs_to_db(session)
    return session


def _row_counts(rows: list[dict[str, int | str]], label_key: str) -> dict[str, int]:
    return {str(row[label_key]): int(row["count"]) for row in rows}
