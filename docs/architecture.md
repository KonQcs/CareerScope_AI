# Architecture

CareerScope AI is a local-first MVP for explainable career matching. It combines a FastAPI API,
a Streamlit user interface, SQLite persistence, deterministic CV parsing, local sample job data,
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
- `backend/app/db`: SQLAlchemy base, session, and table initialization.
- `backend/app/models`: SQLAlchemy models for candidate profiles, skills, projects, jobs, job skills,
  and match results.
- `backend/app/schemas`: Pydantic v2 request and response models.
- `backend/app/services/cv_parser.py`: deterministic TXT/PDF CV parsing and section extraction.
- `backend/app/skill_extraction`: taxonomy-backed skill normalization and text matching.
- `backend/app/job_collector`: sample job ingestion and job-skill extraction.
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
