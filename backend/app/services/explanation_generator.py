from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import httpx

from backend.app.core.config import settings

DEFAULT_LLM_BASE_URL = "https://api.openai.com/v1"
DEFAULT_LLM_MODEL = "gpt-4o-mini"
LLM_TIMEOUT_SECONDS = 20.0

MATCH_RESULT_KEYS = {
    "title",
    "company",
    "location",
    "overall_score",
    "explainable_score",
    "semantic_similarity_score",
    "match_label",
    "matching_skills",
    "missing_skills",
    "weak_skills",
    "required_skill_score",
    "preferred_skill_score",
    "seniority_score",
    "domain_score",
    "portfolio_evidence_score",
    "location_score",
    "explanation",
}
SKILL_GAP_KEYS = {
    "target_field",
    "target_job_title",
    "overall_readiness_score",
    "matching_skills",
    "strong_skills",
    "partial_skills",
    "missing_skills",
    "portfolio_evidenced_skills",
    "cv_only_skills",
    "recommended_projects",
    "recommended_learning_topics",
    "explanation",
}


def generate_user_friendly_explanation(
    match_result: Any,
    skill_gap_report: Any | None = None,
) -> str:
    structured_payload = {
        "match_result": _sanitize_mapping(match_result, MATCH_RESULT_KEYS),
        "skill_gap_report": _sanitize_mapping(skill_gap_report, SKILL_GAP_KEYS)
        if skill_gap_report is not None
        else None,
    }
    fallback_explanation = _deterministic_explanation(structured_payload)

    if not _llm_is_configured():
        return fallback_explanation

    llm_explanation = _generate_with_llm(structured_payload)
    return llm_explanation or fallback_explanation


def _generate_with_llm(payload: dict[str, Any]) -> str | None:
    api_key = _llm_api_key()
    if not api_key:
        return None

    request_payload = {
        "model": settings.llm_model or settings.openai_model or DEFAULT_LLM_MODEL,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You rewrite structured career-match results into a concise, user-friendly "
                    "explanation. Use only the provided JSON. Do not invent skills, jobs, "
                    "companies, scores, or evidence. Do not request or reveal raw CV text."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False, sort_keys=True),
            },
        ],
    }
    endpoint = f"{_llm_base_url().rstrip('/')}/chat/completions"

    try:
        response = httpx.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            json=request_payload,
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    try:
        response_payload = response.json()
    except ValueError:
        return None

    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None

    message = choices[0].get("message") if isinstance(choices[0], Mapping) else None
    content = message.get("content") if isinstance(message, Mapping) else None
    if not isinstance(content, str) or not content.strip():
        return None

    return content.strip()


def _deterministic_explanation(payload: dict[str, Any]) -> str:
    match_result = payload["match_result"]
    skill_gap_report = payload.get("skill_gap_report") or {}
    title = str(match_result.get("title") or "This role")
    company = str(match_result.get("company") or "the company")
    score = _format_score(match_result.get("overall_score"))
    matching_skills = _as_string_list(match_result.get("matching_skills"))
    missing_skills = _as_string_list(match_result.get("missing_skills"))
    weak_skills = _as_string_list(match_result.get("weak_skills"))

    parts = [f"{title} at {company} has a match score of {score}."]

    if matching_skills:
        parts.append(f"Best matches: {_format_list(matching_skills)}.")
    else:
        parts.append("No direct matching skills were identified.")

    if missing_skills:
        parts.append(f"Main gaps: {_format_list(missing_skills)}.")
    else:
        parts.append("No major missing skills were identified.")

    if weak_skills:
        parts.append(f"Needs stronger evidence: {_format_list(weak_skills)}.")

    readiness_score = skill_gap_report.get("overall_readiness_score")
    target_title = skill_gap_report.get("target_job_title")
    if readiness_score is not None and target_title:
        parts.append(f"Overall readiness for {target_title} is {_format_score(readiness_score)}.")

    recommended_projects = _as_string_list(skill_gap_report.get("recommended_projects"))
    if recommended_projects:
        parts.append(f"Suggested next project: {recommended_projects[0]}")

    return " ".join(parts)


def _llm_is_configured() -> bool:
    return bool(_llm_api_key())


def _llm_api_key() -> str | None:
    return settings.openai_api_key or settings.llm_api_key


def _llm_base_url() -> str:
    return settings.llm_base_url or settings.openai_base_url or DEFAULT_LLM_BASE_URL


def _sanitize_mapping(value: Any, allowed_keys: set[str]) -> dict[str, Any]:
    source = _to_mapping(value)
    sanitized: dict[str, Any] = {}
    for key in allowed_keys:
        field_value = source.get(key, _MISSING)
        if field_value is _MISSING:
            continue
        sanitized[key] = _sanitize_value(field_value)
    return sanitized


_MISSING = object()


def _to_mapping(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump()
    return ObjectMapping(value)


class ObjectMapping(Mapping[str, Any]):
    def __init__(self, value: Any) -> None:
        self.value = value

    def __getitem__(self, key: str) -> Any:
        value = getattr(self.value, key, _MISSING)
        if value is _MISSING:
            raise KeyError(key)
        return value

    def __iter__(self):
        return iter(())

    def __len__(self) -> int:
        return 0

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self.value, key, default)


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _sanitize_value(item)
            for key, item in value.items()
            if str(key) in MATCH_RESULT_KEYS | SKILL_GAP_KEYS
        }
    if isinstance(value, list | tuple | set):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


def _format_score(value: Any) -> str:
    try:
        return f"{float(value):.0f}/100"
    except (TypeError, ValueError):
        return "not available"


def _format_list(items: list[str], limit: int = 6) -> str:
    visible_items = items[:limit]
    suffix = "" if len(items) <= limit else f", and {len(items) - limit} more"
    return ", ".join(visible_items) + suffix


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [str(item) for item in value if str(item).strip()]
