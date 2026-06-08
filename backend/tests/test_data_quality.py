from backend.app.services.data_quality import (
    normalize_evidence_source,
    normalize_evidence_strength,
    normalize_job_remote_type,
    normalize_job_seniority,
    validate_candidate_profile,
    validate_candidate_skill,
    validate_job_posting,
    validate_job_skill,
)


def test_valid_candidate_profile_has_no_issues() -> None:
    issues = validate_candidate_profile(
        {
            "email": "ada@example.com",
            "target_field": "Computer Science",
            "target_job_title": "Data Engineer",
        }
    )

    assert issues == []


def test_invalid_candidate_profile_reports_issues() -> None:
    issues = validate_candidate_profile(
        {
            "email": "not-an-email",
            "target_field": "",
            "target_job_title": " ",
        }
    )

    assert "email must be a valid email address." in issues
    assert "target_field must not be empty." in issues
    assert "target_job_title must not be empty." in issues


def test_valid_candidate_skill_has_no_issues() -> None:
    issues = validate_candidate_skill(
        {
            "normalized_skill_name": "Python",
            "evidence_source": "GitHub",
            "evidence_strength": "strong",
        }
    )

    assert issues == []


def test_candidate_skill_accepts_numeric_evidence_strength() -> None:
    assert normalize_evidence_strength(0.4) == "weak"
    assert normalize_evidence_strength(0.65) == "medium"
    assert normalize_evidence_strength(0.9) == "strong"


def test_invalid_candidate_skill_reports_issues() -> None:
    issues = validate_candidate_skill(
        {
            "normalized_skill_name": "",
            "evidence_source": "social_media",
            "evidence_strength": "excellent",
        }
    )

    assert "normalized_skill_name must not be empty." in issues
    assert any("evidence_source" in issue for issue in issues)
    assert any("evidence_strength" in issue for issue in issues)


def test_valid_job_posting_has_no_issues() -> None:
    issues = validate_job_posting(
        {
            "title": "Data Engineer",
            "company": "Northwind Analytics",
            "description": "Build data pipelines.",
            "requirements_text": "",
            "salary_min": 40000,
            "salary_max": 60000,
            "remote_type": "Hybrid",
            "seniority": "Mid",
        }
    )

    assert issues == []


def test_invalid_job_posting_reports_issues() -> None:
    issues = validate_job_posting(
        {
            "title": "",
            "company": " ",
            "description": "",
            "requirements_text": "",
            "salary_min": 70000,
            "salary_max": 60000,
            "remote_type": "Flexible-ish",
            "seniority": "Expert",
        }
    )

    assert "title must not be empty." in issues
    assert "company must not be empty." in issues
    assert "description or requirements_text must not be empty." in issues
    assert "salary_min must not be greater than salary_max." in issues
    assert any("remote_type" in issue for issue in issues)
    assert any("seniority" in issue for issue in issues)


def test_valid_job_skill_has_no_issues() -> None:
    issues = validate_job_skill(
        {
            "normalized_skill_name": "SQL",
            "importance": "required",
        }
    )

    assert issues == []


def test_invalid_job_skill_reports_issues() -> None:
    issues = validate_job_skill(
        {
            "normalized_skill_name": "",
            "importance": "critical",
        }
    )

    assert "normalized_skill_name must not be empty." in issues
    assert any("importance" in issue for issue in issues)


def test_quality_normalizers_accept_aliases() -> None:
    assert normalize_evidence_source("website") == "Portfolio"
    assert normalize_job_remote_type("on site") == "On-site"
    assert normalize_job_seniority("mid-level") == "Mid"
