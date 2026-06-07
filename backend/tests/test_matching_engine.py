from backend.app.matching.service import calculate_job_match


def _candidate_profile(
    seniority_preference: str = "Mid-level",
    location_preference: str = "Athens",
    remote_preference: str = "Hybrid",
) -> dict[str, str]:
    return {
        "target_field": "Computer Science",
        "target_job_title": "Data Engineer",
        "seniority_preference": seniority_preference,
        "location_preference": location_preference,
        "remote_preference": remote_preference,
    }


def _job(seniority: str = "Mid-level") -> dict[str, str]:
    return {
        "title": "Data Engineer",
        "company": "Northwind Analytics",
        "location": "Athens",
        "country": "Greece",
        "remote_type": "Hybrid",
        "seniority": seniority,
        "description": "Build data pipelines for analytics teams.",
    }


def _candidate_skills(*skills: str, evidence_strength: float = 0.9) -> list[dict[str, object]]:
    return [
        {
            "skill_name": skill,
            "normalized_skill_name": skill,
            "evidence_source": "cv",
            "evidence_strength": evidence_strength,
        }
        for skill in skills
    ]


def _job_skills(*skills: str, importance: str = "required") -> list[dict[str, str]]:
    return [
        {
            "skill_name": skill,
            "normalized_skill_name": skill,
            "importance": importance,
            "category": "data_engineering",
        }
        for skill in skills
    ]


def test_perfect_skill_match_gives_high_score() -> None:
    result = calculate_job_match(
        candidate_profile=_candidate_profile(),
        candidate_skills=_candidate_skills("Python", "SQL", "Spark", "Docker"),
        candidate_projects=[{"detected_skills": ["Python", "SQL", "Spark", "Docker"]}],
        job=_job(),
        job_skills=_job_skills("Python", "SQL", "Spark", "Docker"),
    )

    assert result["overall_score"] >= 90
    assert result["required_skill_score"] == 100
    assert result["matching_skills"] == ["Docker", "Python", "Spark", "SQL"]
    assert result["missing_skills"] == []


def test_missing_required_skills_reduce_score() -> None:
    complete_result = calculate_job_match(
        candidate_profile=_candidate_profile(),
        candidate_skills=_candidate_skills("Python", "SQL", "Spark", "Docker"),
        candidate_projects=[{"detected_skills": ["Python", "SQL", "Spark", "Docker"]}],
        job=_job(),
        job_skills=_job_skills("Python", "SQL", "Spark", "Docker"),
    )
    partial_result = calculate_job_match(
        candidate_profile=_candidate_profile(),
        candidate_skills=_candidate_skills("Python", "SQL"),
        candidate_projects=[{"detected_skills": ["Python", "SQL"]}],
        job=_job(),
        job_skills=_job_skills("Python", "SQL", "Spark", "Docker"),
    )

    assert partial_result["overall_score"] < complete_result["overall_score"]
    assert partial_result["required_skill_score"] == 50
    assert partial_result["missing_skills"] == ["Docker", "Spark"]


def test_portfolio_backed_skills_improve_score() -> None:
    without_portfolio = calculate_job_match(
        candidate_profile=_candidate_profile(),
        candidate_skills=_candidate_skills("Python", "SQL", "Spark", "Docker"),
        candidate_projects=[],
        job=_job(),
        job_skills=_job_skills("Python", "SQL", "Spark", "Docker"),
    )
    with_portfolio = calculate_job_match(
        candidate_profile=_candidate_profile(),
        candidate_skills=_candidate_skills("Python", "SQL", "Spark", "Docker"),
        candidate_projects=[{"detected_skills": ["Python", "SQL", "Spark", "Docker"]}],
        job=_job(),
        job_skills=_job_skills("Python", "SQL", "Spark", "Docker"),
    )

    assert with_portfolio["overall_score"] > without_portfolio["overall_score"]
    assert with_portfolio["portfolio_evidence_score"] == 100
    assert without_portfolio["portfolio_evidence_score"] == 35


def test_seniority_mismatch_reduces_score() -> None:
    matching_seniority = calculate_job_match(
        candidate_profile=_candidate_profile(seniority_preference="Junior"),
        candidate_skills=_candidate_skills("Python", "SQL", "Spark", "Docker"),
        candidate_projects=[{"detected_skills": ["Python", "SQL", "Spark", "Docker"]}],
        job=_job(seniority="Junior"),
        job_skills=_job_skills("Python", "SQL", "Spark", "Docker"),
    )
    mismatched_seniority = calculate_job_match(
        candidate_profile=_candidate_profile(seniority_preference="Junior"),
        candidate_skills=_candidate_skills("Python", "SQL", "Spark", "Docker"),
        candidate_projects=[{"detected_skills": ["Python", "SQL", "Spark", "Docker"]}],
        job=_job(seniority="Senior"),
        job_skills=_job_skills("Python", "SQL", "Spark", "Docker"),
    )

    assert mismatched_seniority["seniority_score"] < matching_seniority["seniority_score"]
    assert mismatched_seniority["overall_score"] < matching_seniority["overall_score"]


def test_explanation_includes_matching_and_missing_skills() -> None:
    result = calculate_job_match(
        candidate_profile=_candidate_profile(),
        candidate_skills=_candidate_skills("Python", "SQL"),
        candidate_projects=[{"detected_skills": ["Python", "SQL"]}],
        job=_job(),
        job_skills=_job_skills("Python", "SQL", "Spark", "Docker"),
    )

    assert "Matching skills: Python, SQL" in result["explanation"]
    assert "Missing skills: Docker, Spark" in result["explanation"]
