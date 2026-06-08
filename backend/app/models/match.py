from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.candidate import CandidateProfile
    from backend.app.models.job import JobPosting


class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        index=True,
    )
    overall_score: Mapped[float] = mapped_column(Float)
    explainable_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    semantic_similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    required_skill_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_skill_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    seniority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    domain_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    portfolio_evidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    matching_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    weak_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    candidate: Mapped[CandidateProfile] = relationship(back_populates="match_results")
    job: Mapped[JobPosting] = relationship(back_populates="match_results")
