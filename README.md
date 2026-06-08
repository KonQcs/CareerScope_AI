# CareerScope AI — CV, Portfolio & Job-Market Matching Platform

[![CI](https://github.com/KonQcs/CareerScope_AI/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/KonQcs/CareerScope_AI/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b.svg)
![SQLite](https://img.shields.io/badge/DB-SQLite-003b57.svg)
![OpenAI](https://img.shields.io/badge/LLM-OpenAI_API-orange.svg)

CareerScope AI is an AI-assisted career intelligence platform that analyzes a candidate's CV and portfolio, extracts evidence-backed skills, compares them with job-market requirements, and recommends matching jobs with explainable scores.

The project is built as a practical MVP for students, graduates, and early-career candidates who want to understand what they already prove through their CV/projects and what they still need to build or study for a target role.

---

## Introduction

While I was in the final year of my Computer Science degree, I started looking for roles in the data field, such as **Data Engineer**, **Data Scientist**, and **ML/AI Engineer**. At that time, most of my GitHub portfolio consisted of academic projects, and I had one main question:

> What else should I create, develop, or study in order to gain the correct skills that most job posts ask for?

That question led me to create **CareerScope AI**. The goal is to help students and early-career candidates like me understand how their CV, GitHub repositories, and portfolio projects compare against real job requirements.

Currently, the application does not run as a fully live job-market platform. It can demonstrate the full workflow using **sample jobs**, and it can also fetch external job postings from the **Adzuna API** when API credentials are configured. The matching logic is explainable and deterministic, while user-facing recommendation explanations can be generated through the **OpenAI API** using a configurable mini model such as `gpt-4o-mini`.

---

## What the App Does

CareerScope AI allows a user to:

1. Choose a target career field, such as Computer Science, Finance, Logistics, Marketing, Healthcare, or Engineering.
2. Enter a desired job title, such as Data Engineer, Data Scientist, ML Engineer, Financial Analyst, or Supply Chain Analyst.
3. Upload a CV in PDF or TXT format.
4. Add portfolio links, including GitHub repositories, GitHub profiles, or personal websites.
5. Extract skills from CV text and portfolio evidence.
6. Compare candidate skills against target-role requirements.
7. Identify strong skills, partial skills, and missing skills.
8. Recommend jobs that match the candidate's experience.
9. Explain why each job is recommended and which skills affect the score.

---

## Key Features

- **CV parsing** for PDF and TXT files
- **GitHub and portfolio analysis** using public repository metadata and README content
- **Taxonomy-backed skill extraction** for Computer Science, Finance, and Logistics
- **Skill-gap analysis** for a selected target field and job title
- **Explainable candidate-to-job matching** with component-level scores
- **Ranked job recommendation engine**
- **Job market analytics dashboard**
- **Adzuna API adapter** for optional external job fetching
- **OpenAI-powered explanation layer** for clearer recommendation summaries
- **FastAPI backend** with documented endpoints
- **Streamlit frontend** for the MVP product experience
- **SQLite local database** with optional PostgreSQL support
- **Docker Compose deployment**
- **pytest test suite and GitHub Actions CI**

---

## Demo Screenshots

The screenshots below show a complete local demo of CareerScope AI using a CV, GitHub portfolio links, sample jobs, Adzuna-fetched jobs, skill-gap analysis, and ranked recommendations.

### 1. Candidate creation, CV upload, and portfolio input

![Candidate profile, CV upload, and portfolio input](docs/screenshots/01_create_candidate_cv_portfolio.png)

### 2. GitHub portfolio analysis and detected project skills

![Detected GitHub projects and skills](docs/screenshots/02_portfolio_projects_detected.png)

### 3. External job fetching and analytics overview

![External jobs and analytics overview](docs/screenshots/03_external_jobs_and_analytics_overview.png)

### 4. Job market analytics charts

![Job market analytics charts](docs/screenshots/04_job_market_analytics_charts.png)

### 5. Skill-gap analysis

![Skill gap analysis](docs/screenshots/05_skill_gap_analysis.png)

### 6. Job recommendations

![Top job recommendations](docs/screenshots/06_job_recommendations_top3.png)

Additional recommendation screenshots are available in `docs/screenshots/`:

- `07_job_recommendations_more_results.png`
- `08_job_recommendations_final_result.png`

---

## Architecture

```mermaid
flowchart LR
    A["User Inputs"] --> B["CV Parser"]
    A --> C["Portfolio Analyzer"]
    B --> D["Skill Extraction"]
    C --> D
    E["Sample Jobs / Adzuna API"] --> F["Job Collector"]
    F --> G["Job Skill Extraction"]
    D --> H["Candidate Profile"]
    G --> I["Job Market Data"]
    H --> J["Skill Gap Engine"]
    I --> J
    H --> K["Matching Engine"]
    I --> K
    J --> L["Recommended Skills & Projects"]
    K --> M["Ranked Job Recommendations"]
    M --> N["Optional OpenAI Explanation Layer"]
    L --> O["Streamlit Dashboard"]
    N --> O
```

---

## How Matching Works

The project avoids being only an LLM wrapper. The core recommendation system uses structured and explainable scoring.

```text
overall_score =
    0.40 * required_skill_score
  + 0.20 * preferred_skill_score
  + 0.15 * seniority_score
  + 0.10 * domain_score
  + 0.10 * portfolio_evidence_score
  + 0.05 * location_score
```

The system separates:

- **Strong skills**: skills found in both CV and portfolio/project evidence
- **Partial skills**: skills found only in the CV or weak evidence
- **Missing skills**: skills commonly requested by relevant job postings but absent from the candidate profile
- **Portfolio-evidenced skills**: skills backed by GitHub repositories or project descriptions
- **Recommended projects**: project ideas designed to close missing skill gaps

The OpenAI API layer is optional. It rewrites structured match results into clearer human-readable explanations, but it does not replace the deterministic scoring engine.

---

## Data Sources

CareerScope AI currently supports:

### Local sample data

```text
data/sample/sample_jobs.json
```

These allow the app to run without external credentials.

### Adzuna API

Add credentials to `.env`:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
ADZUNA_COUNTRY=gb
```

Fetched jobs are normalized, deduplicated, enriched with extracted skills, and stored in the same database tables as sample jobs.

### Candidate data

Candidate data comes from:

- uploaded CV files
- GitHub repositories
- portfolio URLs
- target field and target job title preferences

---

## Tech Stack

| Layer | Tools |
|---|---|
| Backend API | FastAPI |
| Frontend | Streamlit |
| Database | SQLite, optional PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Schemas | Pydantic v2 |
| CV parsing | PyMuPDF / text parsing |
| Skill extraction | deterministic taxonomy matching |
| Matching engine | rule-based explainable scoring |
| Optional LLM explanations | OpenAI API, default `gpt-4o-mini` |
| Testing | pytest |
| Linting | ruff |
| Deployment | Docker Compose |
| CI | GitHub Actions |

---

## API Examples

### Create a candidate

```bash
curl -X POST http://localhost:8000/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alex Morgan",
    "email": "alex@example.com",
    "target_field": "Computer Science",
    "target_job_title": "Data Engineer",
    "seniority_preference": "Junior",
    "location_preference": "Remote",
    "remote_preference": "Any"
  }'
```

### Upload a CV

```bash
curl -X POST http://localhost:8000/candidates/1/cv \
  -F "cv=@data/sample/sample_cv_data_engineer.txt"
```

### Analyze portfolio links

```bash
curl -X POST http://localhost:8000/candidates/1/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://github.com/KonQcs/CareerScope_AI",
      "https://github.com/KonQcs/NY-Yellow-Taxi-Analytics-with-Apache-Spark-Hadoop"
    ]
  }'
```

### Import sample jobs

```bash
curl -X POST http://localhost:8000/jobs/import-sample
```

### Fetch external jobs from Adzuna

```bash
curl -X POST http://localhost:8000/jobs/search-external \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "adzuna",
    "query": "Data Engineer",
    "location": "London",
    "country": "gb",
    "page": 1
  }'
```

### Run a skill-gap report

```bash
curl -X POST http://localhost:8000/matching/1/skill-gap \
  -H "Content-Type: application/json" \
  -d '{
    "target_field": "Computer Science",
    "target_job_title": "Data Engineer"
  }'
```

### Recommend jobs

```bash
curl -X POST http://localhost:8000/matching/1/recommend-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "target_field": "Computer Science",
    "target_job_title": "Data Engineer",
    "limit": 10
  }'
```

---

## Example Output

### Skill-gap report

```json
{
  "target_field": "Computer Science",
  "target_job_title": "Data Engineer",
  "overall_readiness_score": 51,
  "strong_skills": ["Python", "SQL", "Spark", "Docker", "ELT", "data quality"],
  "partial_skills": ["Excel", "Power BI"],
  "missing_skills": ["AWS", "BigQuery", "data warehousing", "Databricks", "ETL", "Snowflake"],
  "recommended_projects": [
    "Build an ELT pipeline with Airflow, dbt, PostgreSQL, Great Expectations, Docker, and a dashboard.",
    "Build a streaming analytics pipeline with Kafka, Spark or PySpark, Databricks, and data quality checks."
  ]
}
```

### Job recommendation

```json
{
  "title": "Data Engineer",
  "company": "Example Technology Staffing",
  "location": "Remote",
  "overall_score": 79,
  "matching_skills": ["Python", "SQL"],
  "missing_skills": [],
  "explanation": "This role matches the candidate's target role and includes Python and SQL. The score is reduced mainly by seniority and evidence-strength factors."
}
```

---

## Local Setup

```bash
git clone https://github.com/KonQcs/CareerScope_AI.git
cd CareerScope_AI
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

Create the environment file:

```powershell
Copy-Item .env.example .env
```

For macOS/Linux:

```bash
cp .env.example .env
```

Initialize the database and import sample jobs:

```bash
python scripts/init_db.py
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
API docs:    http://localhost:8000/docs
Streamlit:   http://localhost:8501
```

---

## Environment Variables

SQLite is the default database:

```env
DATABASE_URL=sqlite:///./data/careerscope.db
```

Optional PostgreSQL mode:

```env
DATABASE_URL=postgresql+psycopg://careerscope:careerscope@localhost:5432/careerscope
```

Optional OpenAI explanation layer:

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

Optional Adzuna integration:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
ADZUNA_COUNTRY=gb
```

---

## Docker Setup

```bash
make docker-build
make docker-up
```

Initialize the Docker database:

```bash
docker compose exec backend python scripts/init_db.py
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

---

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

---

## Project Structure

```text
CareerScope_AI/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
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
|-- docker-compose.yml
|-- requirements.txt
|-- pyproject.toml
`-- README.md
```

---

## Roadmap

- Add stronger support for real-time job-market ingestion
- Integrate ESCO or O*NET occupation and skills taxonomies
- Add authentication and saved candidate profiles
- Improve GitHub project evidence scoring
- Add vector search over job descriptions and portfolio projects
- Add a trained role/seniority classifier
- Improve cloud deployment support
- Add a hosted public demo
- Add more fields beyond Computer Science, Finance, and Logistics

---

## Limitations

- The MVP primarily demonstrates the workflow with sample jobs.
- Adzuna integration requires valid API credentials.
- Matching is explainable but approximate; it should support decision-making, not replace human judgment.
- No LinkedIn or Indeed scraping is included.
- External portfolio URLs may fail due to network limits, rate limits, or unavailable pages.
- OpenAI-generated explanations are summaries of structured scoring results and should not be treated as independent evidence.
- Raw private CV text is not sent to the optional LLM explanation layer by default.

---

## Why This Project Matters

CareerScope AI was built from a real student problem: understanding how to move from academic projects to job-ready skills. It combines software engineering, data engineering, NLP-style skill extraction, explainable recommendation systems, API design, and product thinking into one portfolio project.

The long-term goal is to help candidates answer a practical question:

> Based on my CV and portfolio, which jobs fit me now, what am I missing, and what should I build next?
