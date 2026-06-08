from typing import Any

import httpx

from backend.app.services import explanation_generator
from backend.app.services.explanation_generator import generate_user_friendly_explanation


def test_missing_api_key_uses_deterministic_match_template(monkeypatch) -> None:
    monkeypatch.setattr(explanation_generator.settings, "openai_api_key", None)
    monkeypatch.setattr(explanation_generator.settings, "llm_api_key", None)

    explanation = generate_user_friendly_explanation(_match_result())

    assert "Data Engineer at Northwind Analytics has a match score of 82/100." in explanation
    assert "Best matches: Python, SQL, Spark." in explanation
    assert "Main gaps: Airflow, dbt." in explanation
    assert "Needs stronger evidence: Docker." in explanation


def test_missing_api_key_includes_skill_gap_summary(monkeypatch) -> None:
    monkeypatch.setattr(explanation_generator.settings, "openai_api_key", None)
    monkeypatch.setattr(explanation_generator.settings, "llm_api_key", None)

    explanation = generate_user_friendly_explanation(
        _match_result(),
        skill_gap_report={
            "target_job_title": "Data Engineer",
            "overall_readiness_score": 64,
            "recommended_projects": ["Build an ELT pipeline with Airflow and dbt."],
            "raw_cv_text": "private text should not be used",
        },
    )

    assert "Overall readiness for Data Engineer is 64/100." in explanation
    assert "Suggested next project: Build an ELT pipeline with Airflow and dbt." in explanation
    assert "private text" not in explanation


def test_llm_payload_uses_only_structured_whitelisted_data(monkeypatch) -> None:
    captured_payload: dict[str, Any] = {}
    monkeypatch.setattr(explanation_generator.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(explanation_generator.settings, "llm_api_key", None)
    monkeypatch.setattr(explanation_generator.settings, "openai_base_url", "https://example.com")

    def fake_post(*_: Any, **kwargs: Any) -> httpx.Response:
        captured_payload.update(kwargs["json"])
        return httpx.Response(
            200,
            request=httpx.Request("POST", "https://example.com/chat/completions"),
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Structured explanation from mocked provider.",
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    explanation = generate_user_friendly_explanation(
        {
            **_match_result(),
            "raw_cv_text": "do not send",
            "evidence_text": "do not send either",
        }
    )

    assert explanation == "Structured explanation from mocked provider."
    serialized_payload = str(captured_payload)
    assert "raw_cv_text" not in serialized_payload
    assert "evidence_text" not in serialized_payload
    assert "Data Engineer" in serialized_payload
    assert "Northwind Analytics" in serialized_payload


def test_llm_failure_falls_back_to_deterministic_template(monkeypatch) -> None:
    monkeypatch.setattr(explanation_generator.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(explanation_generator.settings, "llm_api_key", None)
    monkeypatch.setattr(explanation_generator.settings, "openai_base_url", "https://example.com")

    def fake_post(*_: Any, **__: Any) -> httpx.Response:
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "post", fake_post)

    explanation = generate_user_friendly_explanation(_match_result())

    assert "Data Engineer at Northwind Analytics has a match score of 82/100." in explanation


def _match_result() -> dict[str, Any]:
    return {
        "title": "Data Engineer",
        "company": "Northwind Analytics",
        "overall_score": 82,
        "matching_skills": ["Python", "SQL", "Spark"],
        "missing_skills": ["Airflow", "dbt"],
        "weak_skills": ["Docker"],
        "explanation": "Existing deterministic explanation.",
    }
