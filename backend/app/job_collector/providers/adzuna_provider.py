from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from typing import Any

import httpx

from backend.app.core.config import settings
from backend.app.job_collector.base import JobProvider
from backend.app.job_collector.classification import (
    classify_job_family,
    classify_job_field,
    classify_seniority,
    normalize_remote_type,
)
from backend.app.services.data_quality import normalize_job_remote_type, normalize_job_seniority

ADZUNA_API_BASE_URL = "https://api.adzuna.com/v1/api/jobs"
ADZUNA_TIMEOUT_SECONDS = 12.0
DEFAULT_RESULTS_PER_PAGE = 20


class AdzunaProvider(JobProvider):
    provider_name = "adzuna"

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        default_country: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.app_id = app_id if app_id is not None else settings.adzuna_app_id
        self.app_key = app_key if app_key is not None else settings.adzuna_app_key
        self.default_country = (
            default_country if default_country is not None else settings.adzuna_country
        )
        self.client = client
        self.last_error: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_key)

    def search_jobs(
        self,
        query: str,
        location: str | None = None,
        country: str | None = None,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        if not self.is_configured:
            self.last_error = "Adzuna credentials are missing."
            return []

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": query,
            "results_per_page": DEFAULT_RESULTS_PER_PAGE,
            "content-type": "application/json",
        }
        if location:
            params["where"] = location

        endpoint = (
            f"{ADZUNA_API_BASE_URL}/{_normalize_country(country or self.default_country)}"
            f"/search/{max(page, 1)}"
        )
        with _http_client(self.client) as client:
            try:
                response = client.get(endpoint, params=params)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                self.last_error = f"Adzuna request failed: {exc}"
                return []

        payload = _json_dict(response)
        results = payload.get("results", [])
        if not isinstance(results, list):
            return []
        return [self.normalize_job(job) for job in results if isinstance(job, dict)]

    def normalize_job(self, raw_job: dict[str, Any]) -> dict[str, Any]:
        title = _text(raw_job.get("title")) or "Untitled role"
        description = _clean_description(_text(raw_job.get("description")))
        company = _nested_text(raw_job, "company", "display_name") or "Unknown company"
        location = _nested_text(raw_job, "location", "display_name")
        country = _country_from_location(raw_job.get("location"))
        field = classify_job_field(title, description)
        job_family = classify_job_family(title, description)
        seniority = normalize_job_seniority(classify_seniority(title, description))
        remote_type = normalize_job_remote_type(
            normalize_remote_type(" ".join([title, location or "", description]))
        )

        return {
            "external_id": f"adzuna:{raw_job.get('id') or raw_job.get('redirect_url') or title}",
            "title": title,
            "company": company,
            "field": field,
            "job_family": job_family,
            "location": location,
            "country": country,
            "remote_type": remote_type,
            "seniority": seniority,
            "salary_min": _float_or_none(raw_job.get("salary_min")),
            "salary_max": _float_or_none(raw_job.get("salary_max")),
            "description": description,
            "requirements_text": description,
            "source": self.provider_name,
            "source_url": _text(raw_job.get("redirect_url")),
            "date_posted": _date_string(raw_job.get("created")),
        }


@contextmanager
def _http_client(client: httpx.Client | None) -> Iterator[httpx.Client]:
    if client is not None:
        yield client
        return

    with httpx.Client(timeout=ADZUNA_TIMEOUT_SECONDS, follow_redirects=True) as created_client:
        yield created_client


def _normalize_country(country: str) -> str:
    return country.strip().casefold() or "gb"


def _nested_text(raw_job: dict[str, Any], parent_key: str, child_key: str) -> str | None:
    parent = raw_job.get(parent_key)
    if not isinstance(parent, dict):
        return None
    return _text(parent.get(child_key))


def _country_from_location(location: Any) -> str | None:
    if not isinstance(location, dict):
        return None

    area = location.get("area")
    if isinstance(area, list) and area:
        return _text(area[0])
    return None


def _clean_description(value: str | None) -> str | None:
    if not value:
        return None
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", without_tags).strip()


def _date_string(value: Any) -> str | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value).split("T")[0]).isoformat()
    except ValueError:
        return None


def _float_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _json_dict(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
