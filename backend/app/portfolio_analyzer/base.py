from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel, Field

from backend.app.skill_extraction.taxonomy import find_skills_in_text, normalize_skill


class PortfolioProject(BaseModel):
    name: str
    url: str
    source: str
    description: str | None = None
    detected_skills: list[str] = Field(default_factory=list)
    evidence_text: str | None = None
    evidence_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    language: str | None = None
    topics: list[str] = Field(default_factory=list)
    stars: int | None = None
    forks: int | None = None
    updated_at: str | None = None


def analyze_portfolio_url(url: str, target_field: str | None = None) -> list[PortfolioProject]:
    normalized_url = normalize_portfolio_url(url)
    if normalized_url is None:
        return []

    if is_github_url(normalized_url):
        from backend.app.portfolio_analyzer.github import (
            analyze_github_profile,
            analyze_github_repository,
            extract_github_repository,
        )

        if extract_github_repository(normalized_url) is not None:
            return analyze_github_repository(normalized_url, target_field=target_field)
        return analyze_github_profile(normalized_url, target_field=target_field)

    from backend.app.portfolio_analyzer.web import analyze_generic_website

    return analyze_generic_website(normalized_url, target_field=target_field)


def normalize_portfolio_links(links: list[str]) -> list[str]:
    normalized_links: list[str] = []
    seen: set[str] = set()

    for link in links:
        normalized_url = normalize_portfolio_url(link)
        if normalized_url is None:
            continue

        dedupe_key = normalized_url.casefold().rstrip("/")
        if dedupe_key in seen:
            continue

        normalized_links.append(normalized_url)
        seen.add(dedupe_key)

    return normalized_links


def normalize_portfolio_url(url: str) -> str | None:
    stripped_url = url.strip()
    if not stripped_url:
        return None

    if "://" not in stripped_url:
        stripped_url = f"https://{stripped_url}"

    parsed_url = urlparse(stripped_url)
    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.netloc
        or any(character.isspace() for character in parsed_url.netloc)
    ):
        return None

    return urlunparse(
        (
            parsed_url.scheme.lower(),
            parsed_url.netloc.lower(),
            parsed_url.path.rstrip("/"),
            "",
            parsed_url.query,
            "",
        )
    )


def is_github_url(url: str) -> bool:
    parsed_url = urlparse(url)
    return parsed_url.netloc.casefold() in {"github.com", "www.github.com"}


def detect_portfolio_skills(
    text: str,
    target_field: str | None = None,
    *,
    include_git: bool = False,
) -> list[str]:
    detected_skills = [
        skill["normalized_skill"] for skill in find_skills_in_text(text, field=target_field)
    ]

    if include_git:
        git_skill = normalize_skill("Git") or "Git"
        if git_skill not in detected_skills:
            detected_skills.append(git_skill)

    return _unique_preserving_order(detected_skills)


def first_evidence_snippet(text: str, target_field: str | None = None) -> str | None:
    skills = find_skills_in_text(text, field=target_field)
    for skill in skills:
        snippet = skill.get("evidence_snippet")
        if snippet:
            return snippet
    return None


def compact_text(*parts: object, limit: int = 1600) -> str:
    text = " ".join(str(part).strip() for part in parts if str(part or "").strip())
    text = " ".join(text.split())
    return text[:limit]


def _unique_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value in seen:
            continue
        unique_values.append(value)
        seen.add(value)
    return unique_values
