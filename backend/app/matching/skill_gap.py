from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from backend.app.matching.scoring import read_value, skill_name
from backend.app.skill_extraction.taxonomy import find_skills_in_text, get_skills_for_field

MAX_TARGET_SKILLS = 14
MIN_JOB_SKILL_COUNT = 1
PROJECT_RECOMMENDATION_LIMIT = 3
GENERIC_PROJECT_TEMPLATE = (
    "Build a portfolio project that demonstrates {skills} with clean documentation, "
    "tests, and a short write-up explaining the tradeoffs."
)
ROLE_PROJECT_TEMPLATES = [
    (
        ("airflow", "dbt", "data quality", "etl", "elt", "postgresql", "docker"),
        "Build an ELT pipeline with Airflow, dbt, PostgreSQL, Great Expectations, "
        "Docker, and a dashboard.",
    ),
    (
        ("spark", "pyspark", "kafka", "databricks"),
        "Build a streaming analytics pipeline with Kafka, Spark or PySpark, "
        "Databricks, and data quality checks.",
    ),
    (
        ("financial modeling", "forecasting", "variance analysis", "budgeting"),
        "Create a finance planning workbook and dashboard covering forecasting, "
        "budgeting, variance analysis, and scenario modeling.",
    ),
    (
        ("supply chain management", "inventory optimization", "route optimization"),
        "Build a supply-chain optimization case study for inventory planning, "
        "route optimization, and service-level tradeoffs.",
    ),
    (
        ("docker", "kubernetes", "fastapi", "rest apis", "ci/cd"),
        "Deploy a production-style API with FastAPI, Docker, CI/CD, and Kubernetes "
        "or a cloud container service.",
    ),
]


def generate_skill_gap_report(
    target_field: str,
    target_job_title: str,
    candidate_skills: Iterable[Any],
    candidate_projects: Iterable[Any],
    job_postings: Iterable[Any] | None = None,
    taxonomy_skills: Iterable[str] | None = None,
) -> dict[str, Any]:
    candidate_skills = list(candidate_skills)
    candidate_projects = list(candidate_projects)
    relevant_jobs = find_relevant_jobs(target_field, target_job_title, job_postings or [])
    target_skills = _target_skills_from_jobs(relevant_jobs, target_field)

    if not target_skills:
        target_skills = list(taxonomy_skills or get_skills_for_field(target_field))

    target_skills = _limit_target_skills(target_skills)
    candidate_skill_index = _candidate_skill_index(candidate_skills)
    portfolio_skill_keys = _portfolio_skill_keys(candidate_projects, candidate_skills)

    strong_skills: list[str] = []
    partial_skills: list[str] = []
    missing_skills: list[str] = []
    portfolio_evidenced_skills: list[str] = []
    cv_only_skills: list[str] = []

    for target_skill in target_skills:
        skill_key = _skill_key(target_skill)
        candidate_skill = candidate_skill_index.get(skill_key)
        has_portfolio_evidence = skill_key in portfolio_skill_keys

        if candidate_skill is None and not has_portfolio_evidence:
            missing_skills.append(target_skill)
            continue

        if candidate_skill is not None and has_portfolio_evidence:
            strong_skills.append(target_skill)
            portfolio_evidenced_skills.append(target_skill)
        else:
            partial_skills.append(target_skill)
            if has_portfolio_evidence:
                portfolio_evidenced_skills.append(target_skill)
            else:
                cv_only_skills.append(target_skill)

    overall_readiness_score = _readiness_score(
        strong_count=len(strong_skills),
        partial_count=len(partial_skills),
        target_count=len(target_skills),
    )
    recommended_projects = recommend_projects_for_missing_skills(missing_skills)
    recommended_learning_topics = missing_skills[:8]
    explanation = _build_gap_explanation(
        target_field=target_field,
        target_job_title=target_job_title,
        relevant_job_count=len(relevant_jobs),
        strong_skills=strong_skills,
        partial_skills=partial_skills,
        missing_skills=missing_skills,
        overall_readiness_score=overall_readiness_score,
    )

    return {
        "target_field": target_field,
        "target_job_title": target_job_title,
        "overall_readiness_score": overall_readiness_score,
        "matching_skills": _sorted_unique([*strong_skills, *partial_skills]),
        "strong_skills": _sorted_unique(strong_skills),
        "partial_skills": _sorted_unique(partial_skills),
        "missing_skills": _sorted_unique(missing_skills),
        "portfolio_evidenced_skills": _sorted_unique(portfolio_evidenced_skills),
        "cv_only_skills": _sorted_unique(cv_only_skills),
        "recommended_projects": recommended_projects,
        "recommended_learning_topics": recommended_learning_topics,
        "explanation": explanation,
    }


def find_relevant_jobs(
    target_field: str,
    target_job_title: str,
    job_postings: Iterable[Any],
) -> list[Any]:
    title_keywords = _title_keywords(target_job_title)
    target_field_text = target_field.casefold()
    relevant_jobs: list[Any] = []

    for job in job_postings:
        job_title = str(read_value(job, "title", "") or "").casefold()
        job_description = str(read_value(job, "description", "") or "").casefold()
        requirements_text = str(read_value(job, "requirements_text", "") or "").casefold()
        searchable_text = f"{job_title} {job_description} {requirements_text}"

        title_word_count = len(title_keywords & set(job_title.split()))
        keyword_word_count = len(title_keywords & set(searchable_text.split()))
        required_overlap = min(2, len(title_keywords))
        title_match = bool(title_keywords) and title_word_count >= required_overlap
        keyword_match = bool(title_keywords) and keyword_word_count >= required_overlap
        field_match = target_field_text in searchable_text

        if title_match or keyword_match or field_match:
            relevant_jobs.append(job)

    return relevant_jobs


def recommend_projects_for_missing_skills(missing_skills: list[str]) -> list[str]:
    if not missing_skills:
        return []

    missing_keys = {_skill_key(skill) for skill in missing_skills}
    recommendations: list[str] = []
    for trigger_skills, recommendation in ROLE_PROJECT_TEMPLATES:
        if missing_keys & set(trigger_skills):
            recommendations.append(recommendation)

    if not recommendations:
        recommendations.append(
            GENERIC_PROJECT_TEMPLATE.format(skills=", ".join(missing_skills[:5]))
        )

    return recommendations[:PROJECT_RECOMMENDATION_LIMIT]


def _target_skills_from_jobs(jobs: list[Any], target_field: str) -> list[str]:
    skill_counts: Counter[str] = Counter()
    display_names: dict[str, str] = {}

    for job in jobs:
        for job_skill in _skills_for_job(job, target_field):
            name = skill_name(job_skill)
            if not name:
                continue
            key = _skill_key(name)
            skill_counts[key] += 1
            display_names.setdefault(key, name)

    common_skills = [
        display_names[key]
        for key, count in skill_counts.most_common()
        if count >= MIN_JOB_SKILL_COUNT
    ]
    return common_skills[:MAX_TARGET_SKILLS]


def _skills_for_job(job: Any, target_field: str) -> list[Any]:
    skills = read_value(job, "skills")
    if skills:
        return list(skills)

    if isinstance(job, Mapping) and job.get("skills"):
        return list(job["skills"])

    searchable_text = " ".join(
        str(read_value(job, key, "") or "") for key in ("title", "description", "requirements_text")
    )
    return find_skills_in_text(searchable_text, field=target_field)


def _candidate_skill_index(candidate_skills: list[Any]) -> dict[str, Any]:
    index: dict[str, Any] = {}
    for candidate_skill in candidate_skills:
        name = skill_name(candidate_skill)
        if name:
            index[_skill_key(name)] = candidate_skill
    return index


def _portfolio_skill_keys(candidate_projects: list[Any], candidate_skills: list[Any]) -> set[str]:
    project_skill_keys: set[str] = set()

    for project in candidate_projects:
        detected_skills = read_value(project, "detected_skills", []) or []
        for detected_skill in detected_skills:
            project_skill_keys.add(_skill_key(str(detected_skill)))

    for candidate_skill in candidate_skills:
        evidence_source = str(read_value(candidate_skill, "evidence_source", "") or "").casefold()
        project_sources = ("project", "portfolio", "github", "kaggle")
        if any(source in evidence_source for source in project_sources):
            name = skill_name(candidate_skill)
            if name:
                project_skill_keys.add(_skill_key(name))

    return project_skill_keys


def _limit_target_skills(target_skills: list[str]) -> list[str]:
    seen: set[str] = set()
    limited_skills: list[str] = []
    for skill in target_skills:
        key = _skill_key(skill)
        if key in seen:
            continue
        limited_skills.append(skill)
        seen.add(key)
        if len(limited_skills) >= MAX_TARGET_SKILLS:
            break
    return limited_skills


def _readiness_score(strong_count: int, partial_count: int, target_count: int) -> float:
    if target_count == 0:
        return 0.0
    score = ((strong_count * 1.0) + (partial_count * 0.55)) / target_count
    return round(score * 100, 2)


def _build_gap_explanation(
    target_field: str,
    target_job_title: str,
    relevant_job_count: int,
    strong_skills: list[str],
    partial_skills: list[str],
    missing_skills: list[str],
    overall_readiness_score: float,
) -> str:
    source_phrase = (
        f"{relevant_job_count} relevant job posting(s)"
        if relevant_job_count
        else f"the {target_field} taxonomy fallback"
    )
    parts = [
        f"Readiness for {target_job_title} is {overall_readiness_score:.0f}/100 "
        f"based on {source_phrase}."
    ]

    if strong_skills:
        parts.append(f"Strong skills with portfolio evidence: {_format_skills(strong_skills)}.")
    if partial_skills:
        parts.append(f"Partial skills found mostly in CV text: {_format_skills(partial_skills)}.")
    if missing_skills:
        parts.append(f"Missing common target-role skills: {_format_skills(missing_skills)}.")
    else:
        parts.append("No common target-role skills are missing.")

    return " ".join(parts)


def _format_skills(skills: list[str], limit: int = 8) -> str:
    visible_skills = skills[:limit]
    suffix = "" if len(skills) <= limit else f", and {len(skills) - limit} more"
    return ", ".join(visible_skills) + suffix


def _title_keywords(target_job_title: str) -> set[str]:
    ignored_words = {"and", "the", "a", "an", "senior", "junior", "mid", "level"}
    return {
        word.strip(".,:/()[]").casefold()
        for word in target_job_title.split()
        if word.strip(".,:/()[]").casefold() not in ignored_words
    }


def _skill_key(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted(set(values), key=str.casefold)
