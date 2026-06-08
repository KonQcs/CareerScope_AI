# Architecture

CareerScope AI is a local-first MVP for explainable career matching. It combines a FastAPI API,
a Streamlit user interface, SQLAlchemy persistence, deterministic CV parsing, local sample job data,
and a transparent scoring engine.

## System Flow

```mermaid
flowchart LR
    A["Candidate Inputs"] --> B["CV Parser / Portfolio Analyzer"]
    B --> C["Skill Extraction"]
    C --> D["Matching Engine"]
    D --> E["Job Recommendations"]
    E --> F["Dashboard"]
```

## Runtime Components

- `frontend/streamlit_app.py`: Streamlit MVP for candidate creation, CV upload, portfolio links,
  sample job import, skill-gap reports, and ranked job recommendations.
- `backend/app/main.py`: FastAPI application factory, CORS setup, and router registration.
- `backend/app/api/routes`: HTTP route modules for health, candidates, jobs, matching, and portfolio.
- `backend/app/db`: SQLAlchemy base, session, table initialization, and database URL handling for
  SQLite or PostgreSQL.
- `backend/app/models`: SQLAlchemy models for candidate profiles, skills, projects, jobs, job skills,
  and match results.
- `backend/app/schemas`: Pydantic v2 request and response models.
- `backend/app/services/cv_parser.py`: deterministic TXT/PDF CV parsing and section extraction.
- `backend/app/services/explanation_generator.py`: optional LLM rewrite layer for structured match
  outputs, with deterministic fallback templates.
- `backend/app/skill_extraction`: taxonomy-backed skill normalization and text matching.
- `backend/app/job_collector`: provider-based job ingestion, sample job loading, optional external
  API adapters, classification, and job-skill extraction.
- `backend/app/matching`: skill-gap analysis, component scoring, explanations, and recommendations.
- `data/taxonomies`: local skill taxonomy for Computer Science, Finance, and Logistics.
- `data/sample`: sample CV and job postings for offline development and CI.

## Data Flow

1. The user creates a candidate profile from the Streamlit UI.
2. The user uploads a CV; the API saves it under `data/raw/uploads/`.
3. The CV parser extracts text, probable identity signals, sections, and skills.
4. Portfolio URLs are normalized and converted into project evidence signals.
5. Sample jobs are imported into SQLite and enriched with extracted job skills.
6. The skill-gap engine compares candidate skills and project evidence against target-role demand.
7. The matching engine computes explainable component scores for each relevant job.
8. Streamlit displays readiness, missing skills, project suggestions, and ranked jobs.

## Job Provider Boundary

Job-market collection is organized around the `JobProvider` interface in
`backend/app/job_collector/base.py`. Providers implement `search_jobs(...)` and
`normalize_job(...)`, returning dictionaries compatible with the internal `JobPosting` shape.

The bundled `SampleJobProvider` searches local sample data for offline development and CI. The
optional `AdzunaProvider` reads `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` from the environment and
normalizes API responses when credentials are available. Missing credentials or request failures
return no jobs instead of crashing the application. Tests use mocked HTTP responses and do not call
real job APIs.

## Scoring Model

The first matcher uses transparent weighted scoring:

```text
overall_score =
    0.40 * required_skill_score
  + 0.20 * preferred_skill_score
  + 0.15 * seniority_score
  + 0.10 * domain_score
  + 0.10 * portfolio_evidence_score
  + 0.05 * location_score
```

This is intentionally explainable and deterministic for the MVP. Future versions can add embeddings,
vector search, role classifiers, or LLM explanations without replacing the current baseline.

Optional LLM explanations must only summarize structured matching outputs such as scores, matched
skills, missing skills, role titles, and recommendations. Raw private CV text is not sent by the
explanation service.

## Persistence

SQLite remains the default MVP database through:

```text
DATABASE_URL=sqlite:///./data/careerscope.db
```

PostgreSQL is optional for local or Docker deployments through:

```text
DATABASE_URL=postgresql+psycopg://careerscope:careerscope@localhost:5432/careerscope
```

Inside Docker Compose, use the `postgres` service host:

```text
DATABASE_URL=postgresql+psycopg://careerscope:careerscope@postgres:5432/careerscope
```

## Deployment

Local Python development runs the API and UI in separate terminals. Docker Compose runs the backend
and frontend on the same Docker network, with Streamlit calling `http://backend:8000`.

SQLite is mounted through:

```text
./data:/app/data
```

## Boundaries

- External paid APIs are not required.
- Tests use sample local data and should run without external network access.
- Portfolio URL analysis is heuristic in the MVP.
- The architecture is ready for real job APIs, PostgreSQL, authentication, and richer analytics.
