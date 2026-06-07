# Architecture

CareerScope AI is organized as a local MVP with a FastAPI backend and Streamlit frontend.

## Components

- `frontend/streamlit_app.py`: MVP user interface for career field selection, target job title entry, CV upload, and portfolio links.
- `backend/app/main.py`: FastAPI application factory and router registration.
- `backend/app/api`: HTTP route definitions.
- `backend/app/core`: application configuration and environment loading.
- `backend/app/db`: SQLAlchemy engine, session, and declarative base.
- `backend/app/models`: database models.
- `backend/app/schemas`: Pydantic request and response schemas.
- `backend/app/services`: orchestration layer for candidate analysis workflows.
- `backend/app/skill_extraction`: CV and text skill extraction.
- `backend/app/portfolio_analyzer`: portfolio link analysis and project evidence extraction.
- `backend/app/matching`: target-role comparison and explainable matching.
- `backend/app/job_collector`: local or external job-market data collection.

## MVP Flow

1. A user submits career field, desired job title, CV, and portfolio links from Streamlit.
2. Streamlit posts the profile payload to FastAPI.
3. FastAPI validates and routes the request to the candidate analysis service.
4. The service returns a placeholder analysis response.
5. Future iterations will persist the candidate profile, parse documents, extract skills, inspect portfolio evidence, and score job matches.

## Future AI Layers

- CV parsing and section detection.
- Skill normalization against field-specific taxonomies.
- Portfolio evidence extraction from GitHub, Kaggle, Medium, and personal websites.
- Role requirement extraction from job descriptions.
- Explainable match scoring with traditional ML first, then optional embeddings.
- Job recommendation ranking and mismatch explanation.
