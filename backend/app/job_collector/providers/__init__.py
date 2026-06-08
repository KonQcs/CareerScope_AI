"""Job provider implementations."""

from backend.app.job_collector.providers.adzuna_provider import AdzunaProvider
from backend.app.job_collector.providers.sample_provider import SampleJobProvider

__all__ = ["AdzunaProvider", "SampleJobProvider"]
