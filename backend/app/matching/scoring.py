from collections.abc import Iterable, Mapping
from typing import Any

REQUIRED_IMPORTANCE = {"required", "must_have", "must-have", "essential"}
PREFERRED_IMPORTANCE = {"preferred", "nice_to_have", "nice-to-have", "optional", "bonus"}
SENIORITY_ALIASES = {
    "intern": "junior",
    "internship": "junior",
    "entry": "junior",
    "entry-level": "junior",
    "entry level": "junior",
    "junior": "junior",
    "jr": "junior",
    "mid": "mid",
    "mid-level": "mid",
    "mid level": "mid",
    "intermediate": "mid",
    "middle": "mid",
    "senior": "senior",
    "sr": "senior",
    "lead": "senior",
    "staff": "senior",
    "principal": "senior",
}
DOMAIN_KEYWORDS = {
    "Finance": ("financial", "finance", "accounting", "valuation", "portfolio"),
    "Logistics": ("supply chain", "logistics", "warehouse", "inventory", "route"),
    "Computer Science": (
        "data engineer",
        "data scientist",
        "ml engineer",
        "machine learning",
        "backend",
        "developer",
        "software",
    ),
}


def calculate_skill_overlap(
    candidate_skills: Iterable[Any],
    job_skills: Iterable[Any],
) -> dict[str, Any]:
    candidate_index = _candidate_skill_index(candidate_skills)
    job_records = _dedupe_skill_records(job_skills)

    if not job_records:
        return {
            "score": 100.0,
            "matching_skills": [],
            "missing_skills": [],
            "weak_skills": [],
        }

    matching_skills: list[str] = []
    missing_skills: list[str] = []
    weak_skills: list[str] = []

    for job_record in job_records:
        candidate_record = candidate_index.get(job_record["key"])
        if candidate_record is None:
            missing_skills.append(job_record["name"])
            continue

        matching_skills.append(job_record["name"])
        if _is_weak_candidate_skill(candidate_record):
            weak_skills.append(job_record["name"])

    score = 100 * len(matching_skills) / len(job_records)
    return {
        "score": _round_score(score),
        "matching_skills": _sorted_unique(matching_skills),
        "missing_skills": _sorted_unique(missing_skills),
        "weak_skills": _sorted_unique(weak_skills),
    }


def score_seniority(candidate_preference: str | None, job_seniority: str | None) -> float:
    candidate_level = _normalize_seniority(candidate_preference)
    job_level = _normalize_seniority(job_seniority)
    if candidate_level is None or job_level is None:
        return 70.0
    if candidate_level == job_level:
        return 100.0

    score_matrix = {
        ("junior", "mid"): 70.0,
        ("junior", "senior"): 35.0,
        ("mid", "junior"): 75.0,
        ("mid", "senior"): 70.0,
        ("senior", "mid"): 75.0,
        ("senior", "junior"): 40.0,
    }
    return score_matrix.get((candidate_level, job_level), 55.0)


def score_location(
    candidate_location: str | None,
    remote_preference: str | None,
    job: Any,
) -> float:
    job_remote_type = _normalize_text(read_value(job, "remote_type"))
    job_location = _normalize_text(read_value(job, "location"))
    job_country = _normalize_text(read_value(job, "country"))
    candidate_location_text = _normalize_text(candidate_location)
    remote_preference_text = _normalize_text(remote_preference)

    scores: list[float] = []
    remote_score = _score_remote_preference(remote_preference_text, job_remote_type)
    if remote_score is not None:
        scores.append(remote_score)

    if candidate_location_text:
        job_place = f"{job_location} {job_country}".strip()
        if _text_contains_either(job_place, candidate_location_text):
            scores.append(100.0)
        elif job_remote_type == "remote":
            scores.append(85.0)
        else:
            scores.append(45.0)

    if not scores:
        return 70.0
    return _round_score(sum(scores) / len(scores))


def score_domain(candidate_profile: Any, job: Any) -> float:
    target_field = _normalize_field(read_value(candidate_profile, "target_field"))
    target_job_title = _normalize_text(read_value(candidate_profile, "target_job_title"))
    job_title = _normalize_text(read_value(job, "title"))
    job_description = _normalize_text(read_value(job, "description"))
    inferred_job_field = _infer_domain(job_title) or _infer_domain(job_description)

    field_score = 70.0
    if target_field and inferred_job_field:
        field_score = 100.0 if target_field == inferred_job_field else 35.0

    title_score = 70.0
    if target_job_title and job_title:
        if _text_contains_either(job_title, target_job_title):
            title_score = 100.0
        elif _share_title_keywords(target_job_title, job_title):
            title_score = 85.0
        else:
            title_score = 45.0

    return _round_score((0.65 * field_score) + (0.35 * title_score))


def score_portfolio_evidence(
    candidate_projects: Iterable[Any],
    matching_skills: Iterable[str],
) -> float:
    matching_skill_keys = {_skill_key(skill) for skill in matching_skills}
    if not matching_skill_keys:
        return 0.0

    project_skill_keys = _project_skill_keys(candidate_projects)
    if not project_skill_keys:
        return 35.0

    backed_skill_count = len(matching_skill_keys & project_skill_keys)
    return _round_score(35 + (65 * backed_skill_count / len(matching_skill_keys)))


def split_job_skills_by_importance(job_skills: Iterable[Any]) -> tuple[list[Any], list[Any]]:
    required_skills: list[Any] = []
    preferred_skills: list[Any] = []

    for job_skill in job_skills:
        importance = _normalize_importance(read_value(job_skill, "importance"))
        if importance in PREFERRED_IMPORTANCE:
            preferred_skills.append(job_skill)
        else:
            required_skills.append(job_skill)

    return required_skills, preferred_skills


def read_value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def skill_name(skill: Any) -> str | None:
    if isinstance(skill, str):
        return skill

    for key in ("normalized_skill_name", "normalized_skill", "skill_name", "skill"):
        value = read_value(skill, key)
        if value:
            return str(value)
    return None


def _candidate_skill_index(candidate_skills: Iterable[Any]) -> dict[str, Any]:
    index: dict[str, Any] = {}
    for candidate_skill in candidate_skills:
        name = skill_name(candidate_skill)
        if name:
            index[_skill_key(name)] = candidate_skill
    return index


def _dedupe_skill_records(skills: Iterable[Any]) -> list[dict[str, str]]:
    seen: set[str] = set()
    records: list[dict[str, str]] = []
    for skill in skills:
        name = skill_name(skill)
        if not name:
            continue

        key = _skill_key(name)
        if key in seen:
            continue

        records.append({"key": key, "name": name})
        seen.add(key)
    return records


def _is_weak_candidate_skill(candidate_skill: Any) -> bool:
    evidence_strength = read_value(candidate_skill, "evidence_strength")
    if evidence_strength is None:
        return False
    try:
        return float(evidence_strength) < 0.55
    except (TypeError, ValueError):
        return False


def _normalize_seniority(value: str | None) -> str | None:
    normalized_value = _normalize_text(value)
    if not normalized_value:
        return None

    for alias, level in SENIORITY_ALIASES.items():
        if alias in normalized_value:
            return level
    return None


def _score_remote_preference(
    remote_preference: str,
    job_remote_type: str,
) -> float | None:
    if not remote_preference:
        return None

    if "flex" in remote_preference or "any" in remote_preference:
        return 85.0

    if "remote" in remote_preference:
        if job_remote_type == "remote":
            return 100.0
        if job_remote_type == "hybrid":
            return 75.0
        return 30.0

    if "hybrid" in remote_preference:
        if job_remote_type == "hybrid":
            return 100.0
        if job_remote_type == "remote":
            return 85.0
        return 60.0

    if "onsite" in remote_preference or "on-site" in remote_preference:
        if job_remote_type in {"onsite", "on-site"}:
            return 100.0
        if job_remote_type == "hybrid":
            return 70.0
        return 60.0

    return None


def _normalize_field(value: Any) -> str | None:
    normalized_value = _normalize_text(value)
    for field in DOMAIN_KEYWORDS:
        if normalized_value == field.casefold():
            return field
    return None


def _infer_domain(text: str) -> str | None:
    for field, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return field
    return None


def _share_title_keywords(candidate_title: str, job_title: str) -> bool:
    ignored_words = {"and", "engineer", "developer", "analyst", "scientist", "senior", "junior"}
    candidate_words = set(candidate_title.split()) - ignored_words
    job_words = set(job_title.split()) - ignored_words
    return bool(candidate_words & job_words)


def _project_skill_keys(candidate_projects: Iterable[Any]) -> set[str]:
    project_skill_keys: set[str] = set()
    for project in candidate_projects:
        detected_skills = read_value(project, "detected_skills", []) or []
        for detected_skill in detected_skills:
            if detected_skill:
                project_skill_keys.add(_skill_key(str(detected_skill)))
    return project_skill_keys


def _normalize_importance(value: Any) -> str:
    return str(value or "required").strip().casefold().replace(" ", "_")


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().casefold()


def _skill_key(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())


def _text_contains_either(left: str, right: str) -> bool:
    return bool(left and right and (left in right or right in left))


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted(set(values), key=str.casefold)


def _round_score(score: float) -> float:
    return round(max(0.0, min(100.0, score)), 2)
