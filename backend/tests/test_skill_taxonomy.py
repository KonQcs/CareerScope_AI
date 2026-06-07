from backend.app.skill_extraction.taxonomy import (
    find_skills_in_text,
    get_skill_category,
    get_skills_for_field,
    normalize_skill,
)


def _skill_names(matches: list[dict[str, str]]) -> set[str]:
    return {match["normalized_skill"] for match in matches}


def test_synonym_normalization() -> None:
    assert normalize_skill("py") == "Python"
    assert normalize_skill("Postgres") == "PostgreSQL"
    assert normalize_skill("continuous integration") == "CI/CD"
    assert normalize_skill("enterprise resource planning") == "ERP"
    assert normalize_skill("not a real skill") is None


def test_get_skill_category_and_field_skills() -> None:
    assert get_skill_category("sklearn") == "machine_learning"
    assert get_skill_category("budget variance") == "finance"

    computer_science_skills = get_skills_for_field("computer science")
    assert "Python" in computer_science_skills
    assert "Kubernetes" in computer_science_skills
    assert "testing" in computer_science_skills


def test_detecting_skills_in_cv_like_text() -> None:
    text = """
    Built FastAPI services in Python with PostgreSQL and MongoDB.
    Containerized workloads with Docker, deployed on Kubernetes, and used
    CI/CD pipelines with pytest-based testing. Created PySpark ETL jobs in
    Databricks and tracked experiments with MLflow.
    """

    matches = find_skills_in_text(text, field="Computer Science")
    skills = _skill_names(matches)

    assert {
        "FastAPI",
        "Python",
        "PostgreSQL",
        "MongoDB",
        "Docker",
        "Kubernetes",
        "CI/CD",
        "testing",
        "PySpark",
        "ETL",
        "Databricks",
        "MLflow",
    }.issubset(skills)
    assert len(skills) == len(matches)
    assert all(match["evidence_snippet"] for match in matches)


def test_detecting_finance_skills() -> None:
    text = """
    Finance analyst with experience in financial modelling, valuation,
    variance analysis, budgeting, forecasting, and risk assessment.
    Built dashboards in PowerBI and queried portfolio data with SQL.
    """

    matches = find_skills_in_text(text, field="Finance")
    skills = _skill_names(matches)

    assert {
        "financial modeling",
        "valuation",
        "variance analysis",
        "budgeting",
        "forecasting",
        "risk analysis",
        "Power BI",
        "SQL",
    }.issubset(skills)


def test_detecting_logistics_skills() -> None:
    text = """
    Logistics specialist focused on SCM, demand planning, warehouse management,
    route optimisation, inventory optimization, and ERP implementation.
    Used Python and Excel for operations research models.
    """

    matches = find_skills_in_text(text, field="Logistics")
    skills = _skill_names(matches)

    assert {
        "supply chain management",
        "demand planning",
        "warehouse management",
        "route optimization",
        "inventory optimization",
        "ERP",
        "Python",
        "Excel",
        "operations research",
    }.issubset(skills)
