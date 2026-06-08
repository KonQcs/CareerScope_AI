from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import models as _models  # noqa: F401
from backend.app.api.routes import jobs as jobs_route
from backend.app.api.routes import matching as matching_route
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.job_collector.providers.adzuna_provider import AdzunaProvider
from backend.app.main import app
from backend.app.services import explanation_generator

SAMPLE_CV_PATH = Path("data/sample/sample_cv_data_engineer.txt")


@pytest.fixture(autouse=True)
def disable_llm_network_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(explanation_generator.settings, "openai_api_key", None)
    monkeypatch.setattr(explanation_generator.settings, "llm_api_key", None)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_candidate(client: TestClient) -> None:
    response = client.post("/candidates", json=_candidate_payload())

    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Alex Morgan"
    assert data["email"] == "alex.api@example.com"
    assert data["target_job_title"] == "Data Engineer"


def test_create_candidate_rejects_invalid_email(client: TestClient) -> None:
    payload = _candidate_payload()
    payload["email"] = "invalid-email"

    response = client.post("/candidates", json=payload)

    assert response.status_code == 422
    assert "email must be a valid email address." in response.json()["detail"]


def test_get_candidate_by_id(client: TestClient) -> None:
    created_response = client.post("/candidates", json=_candidate_payload())
    candidate_id = created_response.json()["id"]

    response = client.get(f"/candidates/{candidate_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == candidate_id
    assert data["email"] == "alex.api@example.com"


def test_import_sample_jobs(client: TestClient) -> None:
    response = client.post("/jobs/import-sample")

    assert response.status_code == 200
    assert response.json() == {"inserted_jobs": 18}


def test_external_job_search_handles_missing_credentials(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        jobs_route,
        "AdzunaProvider",
        lambda: AdzunaProvider(app_id="", app_key=""),
    )

    response = client.post(
        "/jobs/search-external",
        json={
            "provider": "adzuna",
            "query": "Data Engineer",
            "country": "gb",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "adzuna"
    assert data["fetched_jobs"] == 0
    assert data["inserted_jobs"] == 0
    assert data["error"] == "Adzuna credentials are missing."


def test_job_analytics_endpoint_returns_aggregates(client: TestClient) -> None:
    client.post("/jobs/import-sample")

    response = client.get("/jobs/analytics", params={"field": "Computer Science"})

    assert response.status_code == 200
    data = response.json()
    assert data["jobs_by_field"]
    assert data["jobs_by_seniority"]
    assert data["jobs_by_remote_type"]
    assert data["top_skills_overall"]
    assert data["top_skills_by_target_field"]
    assert data["top_companies"]
    assert data["salary_summary"]


def test_recommend_jobs_returns_ranked_results(client: TestClient) -> None:
    candidate_id = _create_candidate_with_cv(client)
    client.post("/jobs/import-sample")

    response = client.post(
        f"/matching/{candidate_id}/recommend-jobs",
        json={
            "target_field": "Computer Science",
            "target_job_title": "Data Engineer",
            "limit": 5,
        },
    )

    assert response.status_code == 200
    recommendations = response.json()
    scores = [recommendation["overall_score"] for recommendation in recommendations]
    assert recommendations
    assert scores == sorted(scores, reverse=True)
    assert any("Data Engineer" in recommendation["title"] for recommendation in recommendations)


def test_recommend_jobs_uses_user_friendly_explanation(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = _create_candidate_with_cv(client)
    client.post("/jobs/import-sample")
    explanation_calls = []

    def fake_explanation(match_result, skill_gap_report=None) -> str:
        explanation_calls.append((match_result, skill_gap_report))
        return f"LLM rewrite for {match_result.title} at {match_result.company}."

    monkeypatch.setattr(
        matching_route,
        "generate_user_friendly_explanation",
        fake_explanation,
    )

    response = client.post(
        f"/matching/{candidate_id}/recommend-jobs",
        json={
            "target_field": "Computer Science",
            "target_job_title": "Data Engineer",
            "limit": 2,
        },
    )

    assert response.status_code == 200
    recommendations = response.json()
    assert len(recommendations) == 2
    assert len(explanation_calls) == 2
    assert recommendations[0]["explanation"].startswith("LLM rewrite for ")


def test_skill_gap_endpoint_returns_missing_and_matching_skills(client: TestClient) -> None:
    candidate_id = _create_candidate_with_cv(client)
    client.post("/jobs/import-sample")

    response = client.post(
        f"/matching/{candidate_id}/skill-gap",
        json={
            "target_field": "Computer Science",
            "target_job_title": "ML Engineer",
        },
    )

    assert response.status_code == 200
    report = response.json()
    assert "Python" in report["matching_skills"]
    assert report["missing_skills"]
    assert report["overall_readiness_score"] > 0


def _create_candidate_with_cv(client: TestClient) -> int:
    candidate_response = client.post("/candidates", json=_candidate_payload())
    candidate_id = candidate_response.json()["id"]

    with SAMPLE_CV_PATH.open("rb") as sample_cv:
        upload_response = client.post(
            f"/candidates/{candidate_id}/cv",
            files={"cv": ("sample_cv_data_engineer.txt", sample_cv, "text/plain")},
        )

    assert upload_response.status_code == 200
    assert upload_response.json()["stored_skill_count"] > 0
    return int(candidate_id)


def _candidate_payload() -> dict[str, str]:
    return {
        "full_name": "Alex Morgan",
        "email": "alex.api@example.com",
        "target_field": "Computer Science",
        "target_job_title": "Data Engineer",
        "seniority_preference": "Mid-level",
        "location_preference": "Athens",
        "remote_preference": "Hybrid",
    }
