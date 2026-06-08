from typing import Any

from backend.app.job_collector.base import JobProvider
from backend.app.job_collector.providers.sample_provider import SampleJobProvider


def collect_jobs_for_role(
    career_field: str,
    job_title: str,
    provider: JobProvider | None = None,
    location: str | None = None,
    country: str | None = None,
    page: int = 1,
) -> list[dict[str, Any]]:
    """Collect normalized jobs through an injectable provider adapter."""
    active_provider = provider or SampleJobProvider()
    query = " ".join(part for part in (career_field, job_title) if part.strip())
    return active_provider.search_jobs(
        query=query,
        location=location,
        country=country,
        page=page,
    )
