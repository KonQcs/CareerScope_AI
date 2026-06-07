"""Skill extraction package for CV and profile text."""

from backend.app.skill_extraction.taxonomy import (
    find_skills_in_text,
    get_skill_category,
    get_skills_for_field,
    load_taxonomy,
    normalize_skill,
)

__all__ = [
    "find_skills_in_text",
    "get_skill_category",
    "get_skills_for_field",
    "load_taxonomy",
    "normalize_skill",
]
