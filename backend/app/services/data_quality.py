from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)

EVIDENCE_SOURCE_ALIASES = {
    "cv": "CV",
    "github": "GitHub",
    "git": "GitHub",
    "portfolio": "Portfolio",
    "website": "Portfolio",
    "web": "Portfolio",
    "kaggle": "Portfolio",
    "medium": "Portfolio",
    "jobposting": "JobPosting",
    "jobpostingdata": "JobPosting",
    "jobpostingtext": "JobPosting",
    "jobpostingrequirement": "JobPosting",
    "jobpost": "JobPosting",
    "manual": "Manual",
    "unknown": "Unknown",
}
EVIDENCE_STRENGTH_LABELS = {"weak", "medium", "strong"}
REMOTE_TYPE_ALIASES = {
    "remote": "Remote",
    "fullyremote": "Remote",
    "remotefirst": "Remote",
    "wfh": "Remote",
    "workfromhome": "Remote",
    "hybrid": "Hybrid",
    "onsite": "On-site",
    "office": "On-site",
    "inoffice": "On-site",
    "any": "Any",
    "flexible": "Any",
    "unknown": "Unknown",
    "anyunknown": "Unknown",
}
SENIORITY_ALIASES = {
    "intern": "Internship",
    "internship": "Internship",
    "trainee": "Internship",
    "junior": "Junior",
    "jr": "Junior",
    "entrylevel": "Junior",
    "entry": "Junior",
    "associate": "Junior",
    "mid": "Mid",
    "midlevel": "Mid",
    "intermediate": "Mid",
    "senior": "Senior",
    "sr": "Senior",
    "lead": "Lead",
    "staff": "Lead",
    "principal": "Lead",
    "manager": "Lead",
    "head": "Lead",
    "any": "Any",
    "unknown": "Unknown",
    "anyunknown": "Unknown",
}
IMPORTANCE_ALIASES = {
    "required": "required",
    "musthave": "required",
    "must": "required",
    "essential": "required",
    "preferred": "preferred",
    "nicetohave": "preferred",
    "optional": "preferred",
    "bonus": "preferred",
    "mentioned": "mentioned",
    "unknown": "unknown",
}


def validate_candidate_profile(data: Any) -> list[str]:
    issues: list[str] = []
    email = _optional_text(_read_value(data, "email"))

    if email and EMAIL_PATTERN.fullmatch(email) is None:
        issues.append("email must be a valid email address.")
    if not _optional_text(_read_value(data, "target_field")):
        issues.append("target_field must not be empty.")
    if not _optional_text(_read_value(data, "target_job_title")):
        issues.append("target_job_title must not be empty.")

    return issues


def validate_candidate_skill(data: Any) -> list[str]:
    issues: list[str] = []

    if not _optional_text(
        _read_value(data, "normalized_skill_name", _read_value(data, "normalized_skill"))
    ):
        issues.append("normalized_skill_name must not be empty.")

    evidence_source = normalize_evidence_source(_read_value(data, "evidence_source"))
    if evidence_source is None:
        issues.append(
            "evidence_source must be one of CV, GitHub, Portfolio, JobPosting, Manual, or Unknown."
        )

    if normalize_evidence_strength(_read_value(data, "evidence_strength")) is None:
        issues.append("evidence_strength must be weak, medium, strong, or a numeric 0-1 score.")

    return issues


def validate_job_posting(data: Any) -> list[str]:
    issues: list[str] = []

    if not _optional_text(_read_value(data, "title")):
        issues.append("title must not be empty.")
    if not _optional_text(_read_value(data, "company")):
        issues.append("company must not be empty.")
    if not _optional_text(_read_value(data, "description")) and not _optional_text(
        _read_value(data, "requirements_text")
    ):
        issues.append("description or requirements_text must not be empty.")

    salary_min = _number_or_none(_read_value(data, "salary_min"))
    salary_max = _number_or_none(_read_value(data, "salary_max"))
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        issues.append("salary_min must not be greater than salary_max.")

    if normalize_job_remote_type(_read_value(data, "remote_type")) is None:
        issues.append("remote_type must be Remote, Hybrid, On-site, Any, or Unknown.")
    if normalize_job_seniority(_read_value(data, "seniority")) is None:
        issues.append("seniority must be Internship, Junior, Mid, Senior, Lead, Any, or Unknown.")

    return issues


def validate_job_skill(data: Any) -> list[str]:
    issues: list[str] = []

    if not _optional_text(
        _read_value(data, "normalized_skill_name", _read_value(data, "normalized_skill"))
    ):
        issues.append("normalized_skill_name must not be empty.")

    if normalize_job_skill_importance(_read_value(data, "importance")) is None:
        issues.append("importance must be required, preferred, mentioned, or unknown.")

    return issues


def normalize_evidence_source(value: Any) -> str | None:
    if value is None:
        return "Unknown"
    return EVIDENCE_SOURCE_ALIASES.get(_choice_key(value))


def normalize_evidence_strength(value: Any) -> str | None:
    if value is None:
        return None

    text = _optional_text(value)
    if text and text.casefold() in EVIDENCE_STRENGTH_LABELS:
        return text.casefold()

    numeric_value = _number_or_none(value)
    if numeric_value is None or not 0 <= numeric_value <= 1:
        return None
    if numeric_value < 0.55:
        return "weak"
    if numeric_value < 0.8:
        return "medium"
    return "strong"


def normalize_job_remote_type(value: Any) -> str | None:
    if value is None:
        return "Unknown"
    return REMOTE_TYPE_ALIASES.get(_choice_key(value))


def normalize_job_seniority(value: Any) -> str | None:
    if value is None:
        return "Unknown"
    return SENIORITY_ALIASES.get(_choice_key(value))


def normalize_job_skill_importance(value: Any) -> str | None:
    if value is None:
        return "unknown"
    return IMPORTANCE_ALIASES.get(_choice_key(value))


def _read_value(data: Any, key: str, default: Any = None) -> Any:
    if isinstance(data, Mapping):
        return data.get(key, default)
    return getattr(data, key, default)


def _optional_text(value: Any) -> str:
    return str(value or "").strip()


def _choice_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def _number_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
