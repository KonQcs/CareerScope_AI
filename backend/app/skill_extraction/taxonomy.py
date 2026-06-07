import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

TAXONOMY_PATH = Path(__file__).resolve().parents[3] / "data" / "taxonomies" / "skills_taxonomy.json"
SNIPPET_RADIUS = 60


@lru_cache
def load_taxonomy() -> dict[str, Any]:
    with TAXONOMY_PATH.open(encoding="utf-8") as taxonomy_file:
        return json.load(taxonomy_file)


def normalize_skill(raw_skill: str) -> str | None:
    lookup = _build_skill_lookup()
    return lookup.get(_canonical_lookup_key(raw_skill))


def get_skill_category(skill: str) -> str | None:
    taxonomy = load_taxonomy()
    normalized_skill = normalize_skill(skill)
    if normalized_skill is None:
        return None

    for entries in taxonomy["fields"].values():
        for entry in entries:
            if entry["skill"] == normalized_skill:
                return entry["category"]
    return None


def get_skills_for_field(field: str) -> list[str]:
    field_name = _resolve_field_name(field)
    if field_name is None:
        return []

    seen: set[str] = set()
    skills: list[str] = []
    for entry in load_taxonomy()["fields"][field_name]:
        normalized_skill = entry["skill"]
        if normalized_skill not in seen:
            skills.append(normalized_skill)
            seen.add(normalized_skill)
    return skills


def find_skills_in_text(text: str, field: str | None = None) -> list[dict[str, str]]:
    if not text.strip():
        return []

    entries = _entries_for_field(field)
    matches: list[dict[str, str]] = []
    seen: set[str] = set()

    for entry in entries:
        normalized_skill = entry["skill"]
        if normalized_skill in seen:
            continue

        matched_term = _find_first_matching_term(text, _terms_for_entry(entry))
        if matched_term is None:
            continue

        match = _find_term_match(text, matched_term)
        if match is None:
            continue

        matches.append(
            {
                "skill": normalized_skill,
                "normalized_skill": normalized_skill,
                "category": entry["category"],
                "matched_text": match.group(0),
                "evidence_snippet": _build_evidence_snippet(text, match.start(), match.end()),
            }
        )
        seen.add(normalized_skill)

    return matches


def _resolve_field_name(field: str) -> str | None:
    normalized_field = field.strip().casefold()
    for field_name in load_taxonomy()["fields"]:
        if field_name.casefold() == normalized_field:
            return field_name
    return None


def _entries_for_field(field: str | None) -> list[dict[str, Any]]:
    taxonomy = load_taxonomy()
    if field is not None:
        field_name = _resolve_field_name(field)
        if field_name is None:
            return []
        return taxonomy["fields"][field_name]

    seen: set[str] = set()
    entries: list[dict[str, Any]] = []
    for field_entries in taxonomy["fields"].values():
        for entry in field_entries:
            if entry["skill"] in seen:
                continue
            entries.append(entry)
            seen.add(entry["skill"])
    return entries


def _build_skill_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for entries in load_taxonomy()["fields"].values():
        for entry in entries:
            normalized_skill = entry["skill"]
            for term in _terms_for_entry(entry):
                lookup[_canonical_lookup_key(term)] = normalized_skill
    return lookup


def _terms_for_entry(entry: dict[str, Any]) -> list[str]:
    return [entry["skill"], *entry.get("synonyms", [])]


def _canonical_lookup_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def _find_first_matching_term(text: str, terms: list[str]) -> str | None:
    ordered_terms = sorted(terms, key=len, reverse=True)
    for term in ordered_terms:
        if _find_term_match(text, term) is not None:
            return term
    return None


def _find_term_match(text: str, term: str) -> re.Match[str] | None:
    pattern = re.compile(rf"(?<![\w+#]){re.escape(term)}(?![\w+#])", re.IGNORECASE)
    return pattern.search(text)


def _build_evidence_snippet(text: str, start: int, end: int) -> str:
    snippet_start = max(start - SNIPPET_RADIUS, 0)
    snippet_end = min(end + SNIPPET_RADIUS, len(text))
    snippet = text[snippet_start:snippet_end]
    return re.sub(r"\s+", " ", snippet).strip()
