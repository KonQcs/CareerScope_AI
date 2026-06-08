import httpx
from backend.app.job_collector.collector import collect_jobs_for_role
from backend.app.job_collector.providers.adzuna_provider import AdzunaProvider
from backend.app.job_collector.providers.sample_provider import SampleJobProvider


def test_sample_provider_searches_local_jobs() -> None:
    provider = SampleJobProvider()

    jobs = provider.search_jobs("Data Engineer", location="Athens")

    assert jobs
    assert all("Data Engineer" in job["title"] for job in jobs)
    assert all(job["field"] == "Computer Science" for job in jobs)


def test_collect_jobs_for_role_uses_injected_provider() -> None:
    provider = SampleJobProvider()

    jobs = collect_jobs_for_role(
        career_field="Computer Science",
        job_title="Backend Developer",
        provider=provider,
    )

    assert jobs
    assert all("Backend" in job["title"] for job in jobs)


def test_adzuna_provider_missing_credentials_fails_gracefully() -> None:
    provider = AdzunaProvider(app_id="", app_key="")

    jobs = provider.search_jobs("Data Engineer")

    assert jobs == []
    assert provider.last_error == "Adzuna credentials are missing."


def test_adzuna_provider_normalizes_raw_job() -> None:
    provider = AdzunaProvider(app_id="app", app_key="key")

    job = provider.normalize_job(_adzuna_raw_job())

    assert job["external_id"] == "adzuna:123"
    assert job["title"] == "Senior ML Engineer"
    assert job["company"] == "Example AI"
    assert job["field"] == "Computer Science"
    assert job["job_family"] == "Machine Learning"
    assert job["seniority"] == "Senior"
    assert job["remote_type"] == "Remote"
    assert job["salary_min"] == 90000
    assert job["salary_max"] == 120000
    assert job["source"] == "adzuna"
    assert job["date_posted"] == "2026-05-20"


def test_adzuna_provider_search_uses_mocked_http_response() -> None:
    client = httpx.Client(transport=httpx.MockTransport(_adzuna_mock_response))
    provider = AdzunaProvider(app_id="app", app_key="key", client=client, default_country="us")

    jobs = provider.search_jobs("ML Engineer", location="Remote", country="us")

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "adzuna:123"
    assert jobs[0]["job_family"] == "Machine Learning"


def _adzuna_mock_response(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/v1/api/jobs/us/search/1"
    assert request.url.params["app_id"] == "app"
    assert request.url.params["app_key"] == "key"
    assert request.url.params["what"] == "ML Engineer"
    assert request.url.params["where"] == "Remote"
    return httpx.Response(200, json={"results": [_adzuna_raw_job()]})


def _adzuna_raw_job() -> dict:
    return {
        "id": "123",
        "title": "Senior ML Engineer",
        "company": {"display_name": "Example AI"},
        "location": {"display_name": "Remote, United States", "area": ["United States"]},
        "salary_min": 90000,
        "salary_max": 120000,
        "description": "<p>Remote machine learning role using Python, PyTorch, and MLflow.</p>",
        "redirect_url": "https://example.com/jobs/123",
        "created": "2026-05-20T10:30:00Z",
    }
