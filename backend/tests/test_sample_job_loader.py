from backend.app import models as _models  # noqa: F401
from backend.app.db.base import Base
from backend.app.job_collector.sample_loader import (
    classify_job_posting_data,
    extract_skills_for_job,
    import_sample_jobs_to_db,
    load_sample_jobs,
)
from backend.app.models.job import JobPosting, JobSkill
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session


def test_sample_jobs_load_correctly() -> None:
    jobs = load_sample_jobs()

    assert len(jobs) == 18
    assert {job["title"] for job in jobs} >= {
        "Data Engineer",
        "Data Scientist",
        "ML Engineer",
        "Backend Developer",
        "Financial Analyst",
        "Supply Chain Analyst",
    }
    assert all(job["external_id"] for job in jobs)


def test_sample_job_classification_is_added_when_missing() -> None:
    classified_job = classify_job_posting_data(
        {
            "external_id": "example",
            "title": "Junior Data Engineer",
            "company": "Example",
            "description": "Build Python SQL ETL pipelines.",
            "requirements_text": "Airflow and dbt.",
            "location": "Remote",
        }
    )

    assert classified_job["field"] == "Computer Science"
    assert classified_job["job_family"] == "Data Engineering"
    assert classified_job["seniority"] == "Junior"
    assert classified_job["remote_type"] == "Remote"


def test_skills_are_extracted_from_job_requirements() -> None:
    job = {
        "title": "Data Engineer",
        "description": "Build data pipelines.",
        "requirements_text": "Python, SQL, Spark, Docker, Airflow, and data quality.",
    }

    skills = extract_skills_for_job(job)
    skill_names = {skill["normalized_skill_name"] for skill in skills}

    assert {"Python", "SQL", "Spark", "Docker"}.issubset(skill_names)
    assert all(skill["importance"] == "required" for skill in skills)


def test_duplicate_external_id_jobs_are_not_inserted_twice() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        first_insert_count = import_sample_jobs_to_db(session)
        second_insert_count = import_sample_jobs_to_db(session)

        job_count = session.scalar(select(func.count()).select_from(JobPosting))
        job_skill_count = session.scalar(select(func.count()).select_from(JobSkill))

    assert first_insert_count == 18
    assert second_insert_count == 0
    assert job_count == 18
    assert job_skill_count is not None
    assert job_skill_count > 0

    with Session(engine) as session:
        stored_job = session.scalar(
            select(JobPosting).where(JobPosting.external_id == "sample-data-engineer-001")
        )

    assert stored_job is not None
    assert stored_job.field == "Computer Science"
    assert stored_job.job_family == "Data Engineering"
