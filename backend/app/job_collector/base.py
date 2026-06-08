from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class JobProvider(ABC):
    """Provider interface for local or external job-market data sources."""

    provider_name: str

    @abstractmethod
    def search_jobs(
        self,
        query: str,
        location: str | None = None,
        country: str | None = None,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Return normalized job dictionaries for a query."""

    @abstractmethod
    def normalize_job(self, raw_job: dict[str, Any]) -> dict[str, Any]:
        """Convert a provider-specific job payload into CareerScope's internal format."""
