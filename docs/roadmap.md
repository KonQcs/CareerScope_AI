# Roadmap

## Phase 1: Project Foundation

- Create repository structure.
- Add FastAPI backend skeleton.
- Add Streamlit MVP form.
- Add SQLite and SQLAlchemy setup.
- Add configuration, linting, tests, and docs.

## Phase 2: Candidate Intake

- Store submitted candidate profiles.
- Persist CV files in local development storage.
- Extract text from TXT, PDF, and DOCX files.
- Validate and normalize portfolio URLs.

## Phase 3: Skill Extraction

- Create initial skill taxonomies by career field.
- Extract explicit skills from CV text.
- Identify project evidence from portfolio links.
- Classify skills as strong, weak, missing, or unknown.

## Phase 4: Role Matching

- Define target-role requirement templates.
- Compare candidate skills against target roles.
- Generate explainable match summaries.
- Add baseline scikit-learn similarity scoring.

## Phase 5: Job Recommendations

- Add sample job postings for local matching.
- Rank jobs by profile fit.
- Explain why each job is or is not a good match.
- Add optional semantic matching with sentence-transformers.

## Phase 6: Product Hardening

- Add authentication and user profile history.
- Improve UI workflows.
- Add richer tests and CI checks.
- Prepare deployment configuration.
