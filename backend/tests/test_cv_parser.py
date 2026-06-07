from pathlib import Path

import pytest

from backend.app.services.cv_parser import (
    extract_candidate_skills_from_cv,
    extract_cv_text,
    parse_candidate_profile_from_text,
)

SAMPLE_CV_PATH = Path("data/sample/sample_cv_data_engineer.txt")


def test_parser_extracts_email() -> None:
    text = extract_cv_text(str(SAMPLE_CV_PATH))
    profile = parse_candidate_profile_from_text(text)

    assert profile["probable_email"] == "alex.morgan@example.com"
    assert profile["probable_name"] == "Alex Morgan"


def test_parser_extracts_expected_data_engineering_skills() -> None:
    text = extract_cv_text(str(SAMPLE_CV_PATH))
    skills = extract_candidate_skills_from_cv(text, target_field="Computer Science")
    skill_names = {skill["normalized_skill"] for skill in skills}

    assert {"Python", "SQL", "Spark", "Docker"}.issubset(skill_names)


def test_parser_extracts_sections_from_sample_cv() -> None:
    text = extract_cv_text(str(SAMPLE_CV_PATH))
    profile = parse_candidate_profile_from_text(text)

    assert any("Real-Time Order Pipeline" in snippet for snippet in profile["project_snippets"])
    assert any("BSc Computer Science" in snippet for snippet in profile["education_snippets"])
    assert any("AWS Certified" in snippet for snippet in profile["certifications"])
    assert any("Data Engineer" in snippet for snippet in profile["work_experience_snippets"])


def test_parser_handles_empty_text_safely() -> None:
    profile = parse_candidate_profile_from_text("")
    skills = extract_candidate_skills_from_cv("")

    assert profile == {
        "probable_name": None,
        "probable_email": None,
        "skills": [],
        "education_snippets": [],
        "project_snippets": [],
        "work_experience_snippets": [],
        "certifications": [],
    }
    assert skills == []


def test_parser_handles_missing_file_with_clear_exception() -> None:
    with pytest.raises(FileNotFoundError, match="CV file not found"):
        extract_cv_text("data/sample/does_not_exist.txt")
