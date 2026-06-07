from __future__ import annotations

import base64
import binascii
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from urllib.parse import urlparse

import httpx

from backend.app.portfolio_analyzer.base import (
    PortfolioProject,
    compact_text,
    detect_portfolio_skills,
    first_evidence_snippet,
    normalize_portfolio_url,
)

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_TIMEOUT_SECONDS = 8.0
MAX_PROFILE_REPOS = 20


def analyze_github_profile(
    url: str,
    target_field: str | None = None,
    client: httpx.Client | None = None,
) -> list[PortfolioProject]:
    username = extract_github_username(url)
    normalized_url = normalize_portfolio_url(url)
    if username is None or normalized_url is None:
        return []

    with _github_client(client) as api_client:
        repos_response = _safe_get(
            api_client,
            f"{GITHUB_API_BASE_URL}/users/{username}/repos",
            params={"sort": "updated", "per_page": MAX_PROFILE_REPOS},
        )
        if repos_response is None:
            return [
                _fallback_github_project(
                    normalized_url,
                    username,
                    "GitHub profile unavailable.",
                )
            ]
        if _is_rate_limited(repos_response):
            return [
                _fallback_github_project(
                    normalized_url,
                    username,
                    "GitHub API rate limit reached.",
                )
            ]
        if repos_response.status_code >= 400:
            return [
                _fallback_github_project(
                    normalized_url,
                    username,
                    f"GitHub profile returned HTTP {repos_response.status_code}.",
                )
            ]

        repos = _json_list(repos_response)
        if not repos:
            return [
                _fallback_github_project(
                    normalized_url,
                    username,
                    "No public repositories found.",
                )
            ]

        projects: list[PortfolioProject] = []
        for repo in repos[:MAX_PROFILE_REPOS]:
            readme_text = _fetch_readme_text(
                api_client,
                owner=str(repo.get("owner", {}).get("login") or username),
                repo=str(repo.get("name") or ""),
            )
            projects.append(_project_from_repo(repo, readme_text, target_field=target_field))

    return projects


def analyze_github_repository(
    url: str,
    target_field: str | None = None,
    client: httpx.Client | None = None,
) -> list[PortfolioProject]:
    repository = extract_github_repository(url)
    normalized_url = normalize_portfolio_url(url)
    if repository is None or normalized_url is None:
        return []

    owner, repo_name = repository
    with _github_client(client) as api_client:
        repo_response = _safe_get(api_client, f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo_name}")
        if repo_response is None:
            return [
                _fallback_github_project(
                    normalized_url,
                    repo_name,
                    "GitHub repository unavailable.",
                )
            ]
        if _is_rate_limited(repo_response):
            return [
                _fallback_github_project(
                    normalized_url,
                    repo_name,
                    "GitHub API rate limit reached.",
                )
            ]
        if repo_response.status_code >= 400:
            return [
                _fallback_github_project(
                    normalized_url,
                    repo_name,
                    f"GitHub repository returned HTTP {repo_response.status_code}.",
                )
            ]

        repo = _json_dict(repo_response)
        readme_text = _fetch_readme_text(api_client, owner=owner, repo=repo_name)

    return [_project_from_repo(repo, readme_text, target_field=target_field)]


def extract_github_username(url: str) -> str | None:
    normalized_url = normalize_portfolio_url(url)
    if normalized_url is None:
        return None

    parsed_url = urlparse(normalized_url)
    if parsed_url.netloc.casefold() not in {"github.com", "www.github.com"}:
        return None

    parts = _path_parts(parsed_url.path)
    if not parts or parts[0].casefold() in _reserved_github_paths():
        return None
    return parts[0]


def extract_github_repository(url: str) -> tuple[str, str] | None:
    normalized_url = normalize_portfolio_url(url)
    if normalized_url is None:
        return None

    parsed_url = urlparse(normalized_url)
    if parsed_url.netloc.casefold() not in {"github.com", "www.github.com"}:
        return None

    parts = _path_parts(parsed_url.path)
    if len(parts) < 2 or parts[0].casefold() in _reserved_github_paths():
        return None

    repo_name = parts[1].removesuffix(".git")
    if not repo_name:
        return None
    return parts[0], repo_name


def _project_from_repo(
    repo: dict[str, Any],
    readme_text: str,
    target_field: str | None = None,
) -> PortfolioProject:
    name = str(repo.get("name") or "GitHub repository")
    description = str(repo.get("description") or "").strip() or None
    language = str(repo.get("language") or "").strip() or None
    topics = [str(topic) for topic in repo.get("topics", []) if str(topic).strip()]
    html_url = str(repo.get("html_url") or "")
    source_url = html_url or _repo_api_fallback_url(repo)

    searchable_text = compact_text(
        name,
        description,
        language,
        " ".join(topics),
        readme_text,
        limit=6000,
    )
    detected_skills = detect_portfolio_skills(
        searchable_text,
        target_field=target_field,
        include_git=True,
    )
    evidence_text = _repo_evidence_text(
        description=description,
        language=language,
        topics=topics,
        readme_text=readme_text,
        target_field=target_field,
    )

    return PortfolioProject(
        name=name,
        url=source_url,
        source="github",
        description=_repo_description(description, language, topics),
        detected_skills=detected_skills,
        evidence_text=evidence_text,
        evidence_strength=_repo_evidence_strength(repo, readme_text, detected_skills),
        language=language,
        topics=topics,
        stars=_int_or_none(repo.get("stargazers_count")),
        forks=_int_or_none(repo.get("forks_count")),
        updated_at=str(repo.get("updated_at") or "") or None,
    )


def _fetch_readme_text(client: httpx.Client, owner: str, repo: str) -> str:
    if not owner or not repo:
        return ""

    response = _safe_get(
        client,
        f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/readme",
        headers={"Accept": "application/vnd.github+json"},
    )
    if response is None or response.status_code == 404 or _is_rate_limited(response):
        return ""
    if response.status_code >= 400:
        return ""

    payload = _json_dict(response)
    content = str(payload.get("content") or "")
    encoding = str(payload.get("encoding") or "").casefold()
    if encoding != "base64" or not content:
        return ""

    try:
        return base64.b64decode(content, validate=False).decode("utf-8", errors="ignore")
    except (binascii.Error, ValueError):
        return ""


def _fallback_github_project(url: str, name: str, reason: str) -> PortfolioProject:
    searchable_text = compact_text(url, name, "GitHub repository profile")
    detected_skills = detect_portfolio_skills(searchable_text, include_git=True)
    return PortfolioProject(
        name=name,
        url=url,
        source="github",
        description=reason,
        detected_skills=detected_skills,
        evidence_text=reason,
        evidence_strength=0.35 if detected_skills else 0.2,
    )


def _repo_description(
    description: str | None,
    language: str | None,
    topics: list[str],
) -> str:
    parts = []
    if description:
        parts.append(description)
    if language:
        parts.append(f"Primary language: {language}.")
    if topics:
        parts.append(f"Topics: {', '.join(topics[:8])}.")
    return " ".join(parts) or "GitHub repository evidence."


def _repo_evidence_text(
    description: str | None,
    language: str | None,
    topics: list[str],
    readme_text: str,
    target_field: str | None,
) -> str:
    snippet = first_evidence_snippet(readme_text, target_field=target_field)
    return compact_text(
        description,
        f"Language: {language}" if language else "",
        f"Topics: {', '.join(topics)}" if topics else "",
        snippet or readme_text[:1000],
    )


def _repo_evidence_strength(
    repo: dict[str, Any],
    readme_text: str,
    detected_skills: list[str],
) -> float:
    strength = 0.3
    if repo.get("description"):
        strength += 0.1
    if repo.get("language"):
        strength += 0.1
    if repo.get("topics"):
        strength += 0.1
    if readme_text.strip():
        strength += 0.2
    if detected_skills:
        strength += min(0.18, 0.04 * len(detected_skills))
    if _int_or_none(repo.get("stargazers_count")) or _int_or_none(repo.get("forks_count")):
        strength += 0.04

    return round(min(strength, 0.95), 2)


def _safe_get(client: httpx.Client, url: str, **kwargs: Any) -> httpx.Response | None:
    try:
        return client.get(url, **kwargs)
    except httpx.HTTPError:
        return None


def _is_rate_limited(response: httpx.Response) -> bool:
    if response.status_code not in {403, 429}:
        return False

    remaining = response.headers.get("x-ratelimit-remaining")
    if remaining == "0":
        return True

    message = str(_json_dict(response).get("message") or "").casefold()
    return "rate limit" in message


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _json_dict(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


@contextmanager
def _github_client(client: httpx.Client | None) -> Iterator[httpx.Client]:
    if client is not None:
        yield client
        return

    with httpx.Client(timeout=GITHUB_TIMEOUT_SECONDS, follow_redirects=True) as created_client:
        yield created_client


def _repo_api_fallback_url(repo: dict[str, Any]) -> str:
    owner = repo.get("owner", {})
    owner_login = owner.get("login") if isinstance(owner, dict) else None
    name = repo.get("name")
    if owner_login and name:
        return f"https://github.com/{owner_login}/{name}"
    return "https://github.com"


def _path_parts(path: str) -> list[str]:
    return [part for part in path.strip("/").split("/") if part]


def _reserved_github_paths() -> set[str]:
    return {
        "about",
        "apps",
        "collections",
        "contact",
        "customer-stories",
        "enterprise",
        "events",
        "explore",
        "features",
        "marketplace",
        "new",
        "organizations",
        "pricing",
        "readme",
        "search",
        "security",
        "settings",
        "sponsors",
        "topics",
        "trending",
    }


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
