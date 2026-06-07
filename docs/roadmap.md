# Roadmap

CareerScope AI is currently a local MVP designed to demonstrate practical product engineering,
explainable matching, and a credible path toward a production career-intelligence platform.

## Completed MVP Foundation

- FastAPI backend with modular routers.
- Streamlit frontend workflow.
- SQLite persistence with SQLAlchemy 2.x.
- Candidate, skill, project, job, job-skill, and match-result models.
- TXT/PDF CV parsing.
- Skill taxonomy for Computer Science, Finance, and Logistics.
- Sample job ingestion.
- Target-role skill-gap reports.
- Explainable candidate-to-job scoring.
- Ranked job recommendations.
- Docker Compose setup.
- GitHub Actions CI configuration.

## Near-Term Improvements

- Add dashboard charts for job-market demand by skill, seniority, location, and role family.
- Improve portfolio analysis for GitHub repositories, Kaggle profiles, websites, and articles.
- Add candidate history and saved analysis sessions.
- Add richer filters for job recommendations.
- Add screenshot assets for portfolio presentation in `docs/screenshots/`.
- Replace placeholder CI badge URLs after publishing the GitHub repository.

## Product Roadmap

- Real job API integration, such as Adzuna, USAJOBS, or other job data providers.
- ESCO/O*NET taxonomy integration for broader and more standardized skill mapping.
- Authentication and user accounts.
- PostgreSQL migration for multi-user persistence.
- ML role classifier for mapping job titles to normalized role families.
- Vector search for semantic CV-to-job and project-to-skill retrieval.
- LLM-generated explanations on top of deterministic scoring outputs.
- Deployed demo with hosted API and UI.

## Technical Hardening

- Alembic migrations.
- Better file storage policy for uploaded CVs.
- Background jobs for portfolio and job ingestion.
- Contract tests for API response schemas.
- More robust frontend error and loading states.
- Observability for scoring decisions and ingestion failures.

## Known Limitations

- MVP uses sample job data.
- Matching is explainable but approximate.
- No LinkedIn or Indeed scraping is included.
- External URLs may fail due to network limits, rate limits, or unavailable pages.
- Skill extraction is deterministic and taxonomy-based; it does not yet understand deeper context.
