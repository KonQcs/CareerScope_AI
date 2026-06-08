from backend.app.job_collector.classification import (
    classify_job_family,
    classify_job_field,
    classify_seniority,
    normalize_remote_type,
)


def test_junior_data_engineer_classification() -> None:
    title = "Junior Data Engineer"
    description = "Build Python SQL ETL pipelines with Airflow and dbt."

    assert classify_job_field(title, description) == "Computer Science"
    assert classify_job_family(title, description) == "Data Engineering"
    assert classify_seniority(title, description) == "Junior"


def test_senior_ml_engineer_classification() -> None:
    title = "Senior ML Engineer"
    description = "Deploy machine learning models with PyTorch and MLflow."

    assert classify_job_field(title, description) == "Computer Science"
    assert classify_job_family(title, description) == "Machine Learning"
    assert classify_seniority(title, description) == "Senior"


def test_financial_risk_analyst_classification() -> None:
    title = "Financial Risk Analyst"
    description = "Own risk analysis, valuation, accounting, and portfolio reporting."

    assert classify_job_field(title, description) == "Finance"
    assert classify_job_family(title, description) == "Financial Analysis"


def test_supply_chain_analyst_classification() -> None:
    title = "Supply Chain Analyst"
    description = "Improve inventory planning, logistics reporting, and route optimization."

    assert classify_job_field(title, description) == "Logistics"
    assert classify_job_family(title, description) == "Supply Chain"


def test_remote_backend_developer_normalizes_remote_type() -> None:
    text = "Remote Backend Developer building REST APIs from anywhere."

    assert normalize_remote_type(text) == "Remote"
