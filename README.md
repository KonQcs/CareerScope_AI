# CareerScope AI

CareerScope AI is an AI-powered CV, portfolio, and job-market matching platform. The MVP helps a candidate describe a target career path, upload a CV, provide portfolio evidence, and receive an explainable view of how well their profile matches a desired role.

The first version focuses on a local developer workflow with a FastAPI backend, Streamlit frontend, SQLite database, and clear module boundaries for skill extraction, portfolio analysis, role matching, and job collection.

## Product Vision

CareerScope AI should help candidates answer practical career questions:

- Which skills in my CV and portfolio match my target role?
- Which skills are missing or weakly evidenced?
- Which jobs fit my current experience level?
- Why is a recommended job a good or poor match?
- What should I learn, build, or document next?

Supported career fields will start with:

- Computer Science
- Logistics
- Finance
- Marketing
- Healthcare
- Engineering

## MVP Capabilities

- Select a career field.
- Enter a desired job title.
- Upload a CV.
- Provide portfolio links such as GitHub, Kaggle, Medium, a personal website, or other URLs.
- Generate an initial candidate analysis preview.
- Prepare the backend structure for future skill extraction, portfolio evidence scoring, role matching, and job recommendation services.

Complex matching logic is intentionally not implemented yet. The current repository establishes a clean foundation for iterative development.

## Tech Stack

- Python 3.11+
- FastAPI
- Streamlit
- SQLite
- SQLAlchemy 2.x
- Pydantic v2
- Pandas
- scikit-learn
- pytest
- ruff
- python-dotenv
- Optional later: sentence-transformers

## Project Structure

```text
CareerScope_AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── skill_extraction/
│   │   ├── matching/
│   │   ├── portfolio_analyzer/
│   │   ├── job_collector/
│   │   └── main.py
│   └── tests/
├── frontend/
│   └── streamlit_app.py
├── data/
│   ├── raw/
│   ├── processed/
│   ├── sample/
│   └── taxonomies/
├── docs/
├── scripts/
└── .github/workflows/
```

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
make install
```

Or run directly:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## Run Locally

Start the API:

```bash
make run-api
```

The API will be available at:

```text
http://localhost:8000
```

Start the Streamlit UI in another terminal:

```bash
make run-ui
```

The UI will be available at:

```text
http://localhost:8501
```

## Development Commands

```bash
make install
make run-api
make run-ui
make test
make lint
make format
```

## API Preview

- `GET /` returns basic application metadata.
- `GET /api/health` returns service health.
- `GET /api/career-fields` returns the initial career field list.
- `POST /api/candidate/analyze` accepts a career field, desired job title, portfolio links, and CV upload, then returns a placeholder analysis preview.

## Next Step

Implement the first real skill extraction pipeline:

1. Parse uploaded CV text.
2. Normalize skills against a small taxonomy.
3. Extract portfolio evidence from supplied links.
4. Compare the candidate profile with target-role requirements.
5. Return explainable match, missing-skill, and weak-evidence results.
