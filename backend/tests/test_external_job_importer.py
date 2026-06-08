from typing import Any

from backend.app import models as _models  # noqa: F401
from backend.app.db.base import Base
from backend.app.job_collector.base import JobProvider
from backend.app.job_collector.external_importer import import_jobs_from_provider
from backend.app.models.job import JobPosting, JobSkill
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session


class FakeJobProvider(JobProvider):
    provider_name = "fake"

    def search_jobs(
        self,
        query: str,
        location: str | None = None,
        country: str | None = None,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        _ = query, location, country, page
        return [
            self.normalize_job(
                {
                    "external_id": "fake-data-engineer-1",
                    "title": "Data Engineer",
                    "company": "Example Data",
                    "location": "Remote",
                    "country": "Greece",
                    "description": "Build Python SQL Spark ETL pipelines.",
                    "requirements_text": "Python, SQL, Spark, Docker, Airflow.",
                    "source_url": "https://example.com/jobs/1",
                    "date_posted": "2026-06-01",
                }
            )
        ]

    def normalize_job(self, raw_job: dict[str, Any]) -> dict[str, Any]:
        return {**raw_job, "source": self.provider_name}


def test_import_jobs_from_provider_inserts_jobs_and_skills() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        result = import_jobs_from_provider(
            session=session,
            provider=FakeJobProvider(),
            query="Data Engineer",
        )
        second_result = import_jobs_from_provider(
            session=session,
            provider=FakeJobProvider(),
            query="Data Engineer",
        )

        job_count = session.scalar(select(func.count()).select_from(JobPosting))
        skill_count = session.scalar(select(func.count()).select_from(JobSkill))

    assert result["fetched_jobs"] == 1
    assert result["inserted_jobs"] == 1
    assert result["skipped_duplicates"] == 0
    assert second_result["inserted_jobs"] == 0
    assert second_result["skipped_duplicates"] == 1
    assert job_count == 1
    assert skill_count is not None
    assert skill_count > 0
