from backend.app.matching.skill_gap import generate_skill_gap_report


def _job(title: str, *skills: str) -> dict[str, object]:
    return {
        "title": title,
        "company": "Example Co",
        "description": "Build practical systems for the target role.",
        "requirements_text": ", ".join(skills),
        "skills": [
            {
                "skill_name": skill,
                "normalized_skill_name": skill,
                "importance": "required",
            }
            for skill in skills
        ],
    }


def _candidate_skill(skill: str, evidence_strength: float = 0.8) -> dict[str, object]:
    return {
        "skill_name": skill,
        "normalized_skill_name": skill,
        "evidence_source": "cv",
        "evidence_strength": evidence_strength,
    }


def test_report_identifies_missing_skills() -> None:
    report = generate_skill_gap_report(
        target_field="Computer Science",
        target_job_title="Data Engineer",
        candidate_skills=[_candidate_skill("Python"), _candidate_skill("SQL")],
        candidate_projects=[{"detected_skills": ["Python"]}],
        job_postings=[
            _job("Data Engineer", "Python", "SQL", "Spark", "Docker", "Airflow"),
            _job("Senior Data Engineer", "Python", "SQL", "Spark", "dbt", "data quality"),
        ],
    )

    assert {"Airflow", "Docker", "Spark", "data quality", "dbt"}.issubset(
        set(report["missing_skills"])
    )
    assert report["overall_readiness_score"] < 60


def test_report_identifies_strong_skills() -> None:
    report = generate_skill_gap_report(
        target_field="Computer Science",
        target_job_title="Data Engineer",
        candidate_skills=[_candidate_skill("Python"), _candidate_skill("SQL")],
        candidate_projects=[{"detected_skills": ["Python"]}],
        job_postings=[_job("Data Engineer", "Python", "SQL", "Spark")],
    )

    assert "Python" in report["strong_skills"]
    assert "Python" in report["portfolio_evidenced_skills"]
    assert "SQL" in report["partial_skills"]
    assert "SQL" in report["cv_only_skills"]


def test_report_generates_relevant_project_recommendations() -> None:
    report = generate_skill_gap_report(
        target_field="Computer Science",
        target_job_title="Data Engineer",
        candidate_skills=[_candidate_skill("Python"), _candidate_skill("SQL")],
        candidate_projects=[],
        job_postings=[_job("Data Engineer", "Python", "SQL", "Airflow", "dbt", "data quality")],
    )

    recommendations = " ".join(report["recommended_projects"])

    assert "Airflow" in recommendations
    assert "dbt" in recommendations
    assert "ELT pipeline" in recommendations


def test_report_works_with_taxonomy_fallback_when_no_jobs_found() -> None:
    report = generate_skill_gap_report(
        target_field="Computer Science",
        target_job_title="Data Engineer",
        candidate_skills=[_candidate_skill("Python")],
        candidate_projects=[{"detected_skills": ["Python"]}],
        job_postings=[],
    )

    assert "Python" in report["strong_skills"]
    assert "SQL" in report["missing_skills"]
    assert report["recommended_learning_topics"]
    assert "taxonomy fallback" in report["explanation"]
