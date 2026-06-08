"""Job collection package for local and external market data sources."""

from backend.app.job_collector.base import JobProvider
from backend.app.job_collector.collector import collect_jobs_for_role
from backend.app.job_collector.providers import AdzunaProvider, SampleJobProvider
from backend.app.job_collector.sample_loader import (
    extract_skills_for_job,
    import_sample_jobs_to_db,
    load_sample_jobs,
)

__all__ = [
    "AdzunaProvider",
    "JobProvider",
    "SampleJobProvider",
    "collect_jobs_for_role",
    "extract_skills_for_job",
    "import_sample_jobs_to_db",
    "load_sample_jobs",
]
