from __future__ import annotations

from typing import Any

from backend.app.job_collector.base import JobProvider
from backend.app.job_collector.sample_loader import classify_job_posting_data, load_sample_jobs

DEFAULT_PAGE_SIZE = 25


class SampleJobProvider(JobProvider):
    provider_name = "sample"

    def search_jobs(
        self,
        query: str,
        location: str | None = None,
        country: str | None = None,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        normalized_jobs = [self.normalize_job(job) for job in load_sample_jobs()]
        filtered_jobs = [
            job
            for job in normalized_jobs
            if _matches_query(job, query)
            and _matches_optional_text(job.get("location"), location)
            and _matches_optional_text(job.get("country"), country)
        ]
        return _page_items(filtered_jobs, page)

    def normalize_job(self, raw_job: dict[str, Any]) -> dict[str, Any]:
        normalized_job = classify_job_posting_data(raw_job)
        normalized_job.setdefault("source", "local_sample")
        return normalized_job


def _matches_query(job: dict[str, Any], query: str) -> bool:
    if not query.strip():
        return True

    query_terms = set(query.casefold().split())
    searchable_text = " ".join(
        str(job.get(key, "") or "")
        for key in ("title", "company", "field", "job_family", "description", "requirements_text")
    ).casefold()
    return all(term in searchable_text for term in query_terms)


def _matches_optional_text(value: Any, expected: str | None) -> bool:
    if not expected:
        return True
    return expected.casefold() in str(value or "").casefold()


def _page_items(items: list[dict[str, Any]], page: int) -> list[dict[str, Any]]:
    safe_page = max(page, 1)
    start = (safe_page - 1) * DEFAULT_PAGE_SIZE
    end = start + DEFAULT_PAGE_SIZE
    return items[start:end]
