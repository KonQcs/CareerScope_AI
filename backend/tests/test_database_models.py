from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from backend.app import models as _models  # noqa: F401
from backend.app.db.base import Base
from backend.app.models.candidate import CandidateProfile
from backend.app.models.job import JobPosting


def test_database_tables_can_be_created() -> None:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(bind=engine)

    table_names = set(inspect(engine).get_table_names())
    assert {
        "candidate_profiles",
        "candidate_skills",
        "candidate_projects",
        "job_postings",
        "job_skills",
        "match_results",
    }.issubset(table_names)


def test_candidate_profile_can_be_inserted() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    candidate = CandidateProfile(
        full_name="Ada Lovelace",
        email="ada@example.com",
        target_field="Computer Science",
        target_job_title="Machine Learning Engineer",
        seniority_preference="Mid-level",
        location_preference="Athens",
        remote_preference="Hybrid",
    )

    with Session(engine) as session:
        session.add(candidate)
        session.commit()

        saved_candidate = session.scalar(
            select(CandidateProfile).where(CandidateProfile.email == "ada@example.com")
        )

    assert saved_candidate is not None
    assert saved_candidate.full_name == "Ada Lovelace"
    assert saved_candidate.target_job_title == "Machine Learning Engineer"


def test_job_posting_can_be_inserted() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    job = JobPosting(
        external_id="job-001",
        title="Data Analyst",
        company="Example Analytics",
        location="Remote",
        country="Greece",
        remote_type="Remote",
        seniority="Junior",
        salary_min=30000,
        salary_max=45000,
        description="Analyze business data and build dashboards.",
        requirements_text="SQL, Python, Excel, communication",
        source="sample",
        source_url="https://example.com/jobs/job-001",
    )

    with Session(engine) as session:
        session.add(job)
        session.commit()

        saved_job = session.scalar(select(JobPosting).where(JobPosting.external_id == "job-001"))

    assert saved_job is not None
    assert saved_job.title == "Data Analyst"
    assert saved_job.company == "Example Analytics"
