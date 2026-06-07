from __future__ import annotations

import re
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

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - exercised only in minimal local environments.
    BeautifulSoup = None  # type: ignore[assignment]

WEB_TIMEOUT_SECONDS = 8.0


def analyze_generic_website(
    url: str,
    target_field: str | None = None,
    client: httpx.Client | None = None,
) -> list[PortfolioProject]:
    normalized_url = normalize_portfolio_url(url)
    if normalized_url is None:
        return []

    with _web_client(client) as web_client:
        response = _safe_get(web_client, normalized_url)

    if response is None or response.status_code >= 400:
        return []

    page = _extract_page_content(response.text)
    searchable_text = compact_text(
        page["title"],
        page["meta_description"],
        page["visible_text"],
        limit=6000,
    )
    detected_skills = detect_portfolio_skills(searchable_text, target_field=target_field)
    evidence_text = first_evidence_snippet(
        searchable_text,
        target_field=target_field,
    ) or compact_text(
        page["meta_description"],
        page["visible_text"],
        limit=1000,
    )

    parsed_url = urlparse(normalized_url)
    return [
        PortfolioProject(
            name=page["title"] or parsed_url.netloc,
            url=normalized_url,
            source="website",
            description=page["meta_description"] or f"Portfolio evidence from {parsed_url.netloc}.",
            detected_skills=detected_skills,
            evidence_text=evidence_text,
            evidence_strength=_website_evidence_strength(page, detected_skills),
        )
    ]


def _extract_page_content(html: str) -> dict[str, str]:
    if BeautifulSoup is None:
        return _extract_page_content_without_bs4(html)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "canvas"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    meta_description = _meta_description(soup)
    visible_text = " ".join(soup.stripped_strings)

    return {
        "title": compact_text(title, limit=180),
        "meta_description": compact_text(meta_description, limit=300),
        "visible_text": compact_text(visible_text, limit=5000),
    }


def _meta_description(soup: Any) -> str:
    description_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if description_tag and description_tag.get("content"):
        return str(description_tag["content"])

    open_graph_tag = soup.find("meta", attrs={"property": re.compile("^og:description$", re.I)})
    if open_graph_tag and open_graph_tag.get("content"):
        return str(open_graph_tag["content"])

    return ""


def _extract_page_content_without_bs4(html: str) -> dict[str, str]:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    meta_match = re.search(
        r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']+)[\"']",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    visible_text = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    visible_text = re.sub(r"<[^>]+>", " ", visible_text)
    visible_text = re.sub(r"\s+", " ", visible_text).strip()

    return {
        "title": compact_text(
            _unescape_html(title_match.group(1)) if title_match else "",
            limit=180,
        ),
        "meta_description": compact_text(
            _unescape_html(meta_match.group(1)) if meta_match else "",
            limit=300,
        ),
        "visible_text": compact_text(_unescape_html(visible_text), limit=5000),
    }


def _website_evidence_strength(page: dict[str, str], detected_skills: list[str]) -> float:
    strength = 0.25
    if page["title"]:
        strength += 0.05
    if page["meta_description"]:
        strength += 0.1
    if len(page["visible_text"]) > 300:
        strength += 0.15
    if detected_skills:
        strength += min(0.35, 0.08 * len(detected_skills))
    return round(min(strength, 0.85), 2)


def _safe_get(client: httpx.Client, url: str) -> httpx.Response | None:
    try:
        return client.get(url)
    except httpx.HTTPError:
        return None


@contextmanager
def _web_client(client: httpx.Client | None) -> Iterator[httpx.Client]:
    if client is not None:
        yield client
        return

    with httpx.Client(timeout=WEB_TIMEOUT_SECONDS, follow_redirects=True) as created_client:
        yield created_client


def _unescape_html(value: str) -> str:
    return (
        value.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
