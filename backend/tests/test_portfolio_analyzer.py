import base64

import httpx
from backend.app.portfolio_analyzer.base import analyze_portfolio_url
from backend.app.portfolio_analyzer.github import (
    analyze_github_profile,
    analyze_github_repository,
    extract_github_repository,
    extract_github_username,
)
from backend.app.portfolio_analyzer.web import analyze_generic_website


def test_github_username_extraction() -> None:
    assert extract_github_username("https://github.com/KonQcs") == "KonQcs"
    assert extract_github_username("github.com/KonQcs/") == "KonQcs"
    assert extract_github_username("https://example.com/KonQcs") is None


def test_github_repository_extraction() -> None:
    assert extract_github_repository("https://github.com/KonQcs/CareerScope_AI") == (
        "KonQcs",
        "CareerScope_AI",
    )
    assert extract_github_repository("https://github.com/KonQcs/CareerScope_AI.git") == (
        "KonQcs",
        "CareerScope_AI",
    )
    assert extract_github_repository("https://github.com/KonQcs") is None


def test_github_profile_repo_parsing_with_mocked_api() -> None:
    client = httpx.Client(transport=httpx.MockTransport(_github_mock_response))

    projects = analyze_github_profile(
        "https://github.com/alex",
        target_field="Computer Science",
        client=client,
    )

    assert len(projects) == 1
    project = projects[0]
    assert project.name == "data-pipeline"
    assert project.url == "https://github.com/alex/data-pipeline"
    assert project.language == "Python"
    assert project.topics == ["airflow", "dbt", "postgresql"]
    assert project.stars == 12
    assert project.forks == 3
    assert project.evidence_strength > 0.7
    assert {"Airflow", "dbt", "PostgreSQL", "Python", "Docker", "Git"} <= set(
        project.detected_skills
    )


def test_github_repository_detects_skills_from_readme_text() -> None:
    client = httpx.Client(transport=httpx.MockTransport(_github_mock_response))

    projects = analyze_github_repository(
        "https://github.com/alex/data-pipeline",
        target_field="Computer Science",
        client=client,
    )

    assert len(projects) == 1
    assert "Spark" in projects[0].detected_skills
    assert "data quality" in projects[0].detected_skills


def test_generic_website_skill_detection_with_mocked_response() -> None:
    html = """
    <html>
      <head>
        <title>Alex Morgan Portfolio</title>
        <meta name="description" content="FastAPI and PostgreSQL backend projects.">
      </head>
      <body>
        <h1>Data portfolio</h1>
        <p>I build Python APIs with Docker, SQL, Pandas, and cloud deployment.</p>
      </body>
    </html>
    """

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=html.encode(),
            headers={"content-type": "text/html"},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))

    projects = analyze_generic_website(
        "https://example.com",
        target_field="Computer Science",
        client=client,
    )

    assert len(projects) == 1
    assert projects[0].name == "Alex Morgan Portfolio"
    assert {"FastAPI", "PostgreSQL", "Python", "Docker", "SQL", "Pandas"} <= set(
        projects[0].detected_skills
    )


def test_invalid_url_handling() -> None:
    assert analyze_generic_website("not a url") == []
    assert analyze_portfolio_url("ftp://example.com/project") == []


def _github_mock_response(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/users/alex/repos":
        return httpx.Response(
            200,
            json=[
                {
                    "name": "data-pipeline",
                    "html_url": "https://github.com/alex/data-pipeline",
                    "description": "Airflow and dbt ELT pipeline with PostgreSQL.",
                    "language": "Python",
                    "topics": ["airflow", "dbt", "postgresql"],
                    "stargazers_count": 12,
                    "forks_count": 3,
                    "updated_at": "2026-01-15T12:00:00Z",
                    "owner": {"login": "alex"},
                }
            ],
        )

    if request.url.path == "/repos/alex/data-pipeline":
        return httpx.Response(
            200,
            json={
                "name": "data-pipeline",
                "html_url": "https://github.com/alex/data-pipeline",
                "description": "Airflow and dbt ELT pipeline with PostgreSQL.",
                "language": "Python",
                "topics": ["airflow", "dbt", "postgresql"],
                "stargazers_count": 12,
                "forks_count": 3,
                "updated_at": "2026-01-15T12:00:00Z",
                "owner": {"login": "alex"},
            },
        )

    if request.url.path == "/repos/alex/data-pipeline/readme":
        readme = """
        # Data Pipeline

        Production-style ETL and ELT project using Python, Airflow, dbt,
        PostgreSQL, Docker, Spark, and data quality checks.
        """
        return httpx.Response(
            200,
            json={
                "content": base64.b64encode(readme.encode()).decode(),
                "encoding": "base64",
            },
        )

    return httpx.Response(404, json={"message": "Not found"})
