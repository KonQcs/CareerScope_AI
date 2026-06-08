# CareerScope AI — CV, Portfolio & Job-Market Matching Platform

[![CI](https://github.com/KonQcs/CareerScope_AI/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/KonQcs/CareerScope_AI/actions/workflows/ci.yml)

CareerScope AI analyzes a candidate's CV and portfolio, maps skills to target roles, compares
them against job-market demand, identifies missing skills, and recommends matching jobs with
explainable scores.

The project is built as a recruiter-friendly MVP that demonstrates backend API design, local data
ingestion, deterministic NLP-style parsing, explainable scoring, Streamlit product UX, Dockerized
deployment, and CI-ready Python engineering.

## Features

- CV parsing for TXT and PDF files
- GitHub and portfolio link analysis
- taxonomy-backed skill extraction
- target-role skill-gap analysis
- explainable candidate-to-job matching
- ranked job recommendation engine
- job market analytics dashboard foundation
- FastAPI backend
- Streamlit frontend
- SQLite local MVP storage with optional PostgreSQL support
- Docker Compose deployment
- tests and GitHub Actions CI

## Architecture

```mermaid
flowchart LR
    A["Candidate Inputs"] --> B["CV Parser / Portfolio Analyzer"]
    B --> C["Skill Extraction"]
    C --> D["Matching Engine"]
    D --> E["Job Recommendations"]
    E --> F["Dashboard"]
```

## Tech Stack

- Python 3.11+
- FastAPI
- Streamlit
- SQLite
- PostgreSQL optional
- SQLAlchemy 2.x
- Pydantic v2
- Pandas
- scikit-learn
- PyMuPDF
- pytest
- ruff
- Docker Compose

## Screenshots

Screenshots are intended to live in:

```text
docs/screenshots/
```

Suggested portfolio screenshots:

- `docs/screenshots/01_candidate_profile.png`
- `docs/screenshots/02_cv_skills.png`
- `docs/screenshots/03_skill_gap.png`
- `docs/screenshots/04_job_recommendations.png`

## API Examples

Create a candidate:

```bash
curl -X POST http://localhost:8000/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alex Morgan",
    "email": "alex@example.com",
    "target_field": "Computer Science",
    "target_job_title": "Data Engineer",
    "seniority_preference": "Mid",
    "location_preference": "Athens",
    "remote_preference": "Hybrid"
  }'
```

Upload a CV:

```bash
curl -X POST http://localhost:8000/candidates/1/cv \
  -F "cv=@data/sample/sample_cv_data_engineer.txt"
```

Analyze portfolio links:

```bash
curl -X POST http://localhost:8000/candidates/1/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://github.com/example/data-pipeline",
      "https://example.com/portfolio"
    ]
  }'
```

Run a skill-gap report:

```bash
curl -X POST http://localhost:8000/matching/1/skill-gap \
  -H "Content-Type: application/json" \
  -d '{
    "target_field": "Computer Science",
    "target_job_title": "Data Engineer"
  }'
```

Recommend jobs:

```bash
curl -X POST http://localhost:8000/matching/1/recommend-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "target_field": "Computer Science",
    "target_job_title": "Data Engineer",
    "limit": 10
  }'
```

Fetch external jobs through a configured provider:

```bash
curl -X POST http://localhost:8000/jobs/search-external \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "adzuna",
    "query": "Data Engineer",
    "location": "Athens",
    "country": "gb",
    "page": 1
  }'
```

## Job Provider Adapters

CareerScope AI uses a provider interface for job-market data instead of hardcoding one API source.
The offline MVP still imports `data/sample/sample_jobs.json`, while future or credentialed providers
can implement `JobProvider` in `backend/app/job_collector/providers/`.

Included providers:

- `SampleJobProvider`: searches the bundled local sample jobs.
- `AdzunaProvider`: optional real API adapter that normalizes Adzuna results into the internal
  `JobPosting` shape.

Real Adzuna API usage requires credentials. Add these to `.env`:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
ADZUNA_COUNTRY=gb
```

If credentials are missing or an API request fails, the Adzuna adapter returns no jobs and records a
provider error instead of crashing the app. Tests use mocks and do not call external job APIs.

In Streamlit, use **Fetch jobs from Adzuna** in the job import section after adding credentials to
`.env`. Fetched jobs are normalized, validated, deduplicated by `external_id`, enriched with
taxonomy skills, and stored in the same jobs table as sample jobs.

## Optional LLM Explanations

The core matching and skill-gap logic remains deterministic. Optional LLM support only rewrites or
summarizes structured match results that the existing engine already produced.

Without an API key, CareerScope AI uses deterministic template explanations. To enable an
OpenAI-compatible provider, configure:

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

When configured, `POST /matching/{candidate_id}/recommend-jobs` rewrites the explanations for the
ranked recommendations returned to the frontend.

Privacy boundary: the explanation service sends only whitelisted structured fields such as scores,
matched skills, missing skills, job title, and company. It does not send raw private CV text or
project evidence text unless a future feature explicitly opts into that behavior.

## Example Output

Sample skill-gap report:

```json
{
  "target_field": "Computer Science",
  "target_job_title": "Data Engineer",
  "overall_readiness_score": 72.5,
  "strong_skills": ["Python", "SQL", "Docker"],
  "partial_skills": ["Spark", "PostgreSQL"],
  "missing_skills": ["Airflow", "dbt", "data quality", "Kafka"],
  "portfolio_evidenced_skills": ["Python", "Docker"],
  "recommended_projects": [
    "Build an ELT pipeline with Airflow, dbt, PostgreSQL, Great Expectations, Docker, and a dashboard."
  ],
  "recommended_learning_topics": ["Airflow", "dbt", "data quality", "Kafka"],
  "explanation": "Readiness for Data Engineer is 72/100 based on relevant job postings."
}
```

Sample job recommendation:

```json
{
  "title": "Data Engineer",
  "company": "Northwind Analytics",
  "location": "Athens",
  "overall_score": 86.5,
  "match_label": "strong",
  "matching_skills": ["Python", "SQL", "Spark", "Docker"],
  "missing_skills": ["Airflow"],
  "explanation": "Matching skills and portfolio evidence are strong, but Airflow is a gap."
}
```

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install requirements:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copy environment defaults:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## Database Modes

SQLite is the default local MVP database and needs no external service:

```env
DATABASE_URL=sqlite:///./data/careerscope.db
```

PostgreSQL is optional. For a local PostgreSQL server, set:

```env
DATABASE_URL=postgresql+psycopg://careerscope:careerscope@localhost:5432/careerscope
```

For Docker Compose PostgreSQL, the backend connects to the Compose service name:

```env
DATABASE_URL=postgresql+psycopg://careerscope:careerscope@postgres:5432/careerscope
POSTGRES_DB=careerscope
POSTGRES_USER=careerscope
POSTGRES_PASSWORD=careerscope
```

After changing database mode, initialize tables and import sample jobs again:

```bash
python scripts/init_db.py
python scripts/import_sample_jobs.py
```

Initialize the database:

```bash
python scripts/init_db.py
```

Import sample jobs:

```bash
python scripts/import_sample_jobs.py
```

Run the backend:

```bash
make run-api
```

Run the frontend in a second terminal:

```bash
make run-ui
```

Open:

```text
Backend API: http://localhost:8000
API docs: http://localhost:8000/docs
Streamlit UI: http://localhost:8501
```

## Docker Setup

Build and start both services:

```bash
make docker-build
make docker-up
```

This uses SQLite unless `DATABASE_URL` points elsewhere.

To run Docker with PostgreSQL, set `DATABASE_URL` in `.env` to the Compose service URL shown above,
then start with the optional profile:

```bash
docker compose --profile postgres up --build
```

Initialize the Docker database:

```bash
docker compose exec backend python scripts/init_db.py
```

Import sample jobs into the Docker database:

```bash
docker compose exec backend python scripts/import_sample_jobs.py
```

View logs:

```bash
make docker-logs
```

Stop services:

```bash
make docker-down
```

Docker exposes:

```text
Backend API: http://localhost:8000
Streamlit UI: http://localhost:8501
```

The Docker frontend calls the backend through the Compose service network at:

```text
http://backend:8000
```

## Development Commands

```bash
make install
make run-api
make run-ui
make test
make lint
make format
make docker-build
make docker-up
make docker-down
make docker-logs
```

## Project Structure

```text
CareerScope_AI/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- db/
|   |   |-- job_collector/
|   |   |-- matching/
|   |   |-- models/
|   |   |-- portfolio_analyzer/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- skill_extraction/
|   `-- tests/
|-- frontend/
|   `-- streamlit_app.py
|-- data/
|   |-- sample/
|   `-- taxonomies/
|-- docs/
|   |-- screenshots/
|   |-- architecture.md
|   |-- data_model.md
|   `-- roadmap.md
|-- scripts/
|-- Dockerfile.backend
|-- Dockerfile.frontend
`-- docker-compose.yml
```

## Roadmap

- real job API integration
- ESCO/O*NET taxonomy integration
- authentication
- PostgreSQL deployment hardening
- ML role classifier
- vector search
- LLM-generated explanations
- deployed demo

## Limitations

- MVP uses sample job data.
- Matching is explainable but approximate.
- No LinkedIn or Indeed scraping is included.
- External URLs may fail due to network limits, rate limits, or unavailable pages.
- Optional LLM explanations can improve wording, but they must not invent skills, jobs, companies,
  or evidence and should be treated as summaries of deterministic results.
