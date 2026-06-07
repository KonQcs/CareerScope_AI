from backend.app.skill_extraction.taxonomy import find_skills_in_text


def extract_skills_from_text(text: str) -> list[str]:
    """Placeholder for taxonomy-backed skill extraction."""
    return [match["normalized_skill"] for match in find_skills_in_text(text)]
