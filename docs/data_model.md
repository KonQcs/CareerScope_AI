# Data Model

CareerScope AI starts with six core tables for candidate intake, portfolio evidence, job data, and explainable matching.

## CandidateProfile

Stores the candidate's identity and target-role preferences.

| Field | Notes |
| --- | --- |
| `id` | Primary key |
| `full_name` | Candidate display name |
| `email` | Unique candidate email |
| `target_field` | Career field, such as Computer Science or Finance |
| `target_job_title` | Desired role title |
| `seniority_preference` | Preferred level, such as Junior, Mid-level, or Senior |
| `location_preference` | Preferred city, region, or country |
| `remote_preference` | Remote, hybrid, onsite, or flexible preference |
| `created_at` | Submission timestamp |

## CandidateSkill

Stores extracted or inferred skills connected to a candidate.

| Field | Notes |
| --- | --- |
| `candidate_id` | Foreign key to `candidate_profiles.id` |
| `skill_name` | Original skill label |
| `normalized_skill_name` | Canonical skill label used for matching |
| `category` | Domain, tool, language, soft skill, or other grouping |
| `evidence_source` | CV, GitHub, Kaggle, Medium, website, or manual source |
| `evidence_text` | Supporting text or project evidence |
| `evidence_strength` | Numeric evidence confidence or strength |

## CandidateProject

Stores project-level evidence from portfolio links or CV entries.

| Field | Notes |
| --- | --- |
| `candidate_id` | Foreign key to `candidate_profiles.id` |
| `project_name` | Project title |
| `source_url` | Portfolio URL |
| `description` | Project summary |
| `detected_skills` | JSON list of skills detected from the project |
| `evidence_strength` | Numeric evidence score |

## JobPosting And JobSkill

`JobPosting` stores normalized role data from sample files or future collectors. `JobSkill` stores
extracted requirements for each posting, including skill importance and supporting requirement text.

| Field | Notes |
| --- | --- |
| `field` | Deterministic career-field classification, such as Computer Science or Finance |
| `job_family` | Deterministic role-family classification, such as Data Engineering or Supply Chain |
| `remote_type` | Normalized Remote, Hybrid, On-site, or unknown value |
| `seniority` | Normalized seniority label when available or classifiable |

## MatchResult

Stores explainable candidate-to-job scoring.

| Field | Notes |
| --- | --- |
| `overall_score` | Aggregate match score |
| `explainable_score` | Deterministic matching score before semantic blending |
| `semantic_similarity_score` | Optional TF-IDF or sentence-transformer text similarity score |
| `required_skill_score` | Required-skill fit |
| `preferred_skill_score` | Preferred-skill fit |
| `seniority_score` | Seniority alignment |
| `domain_score` | Career-field/domain alignment |
| `portfolio_evidence_score` | Strength of project evidence |
| `location_score` | Location and remote preference alignment |
| `missing_skills` | JSON list of missing skills |
| `matching_skills` | JSON list of matched skills |
| `weak_skills` | JSON list of weakly evidenced skills |

## Storage Approach

The MVP defaults to SQLite in `data/careerscope.db`, controlled by `DATABASE_URL`. PostgreSQL is
also supported by setting `DATABASE_URL` to a `postgresql+psycopg://...` connection string. Raw
uploaded or collected files should stay in `data/raw` during local development and should not be
committed.
