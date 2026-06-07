from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.match import MatchResult


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    external_id: Mapped[str | None] = mapped_column(String(150), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(180), index=True)
    company: Mapped[str] = mapped_column(String(180), index=True)
    location: Mapped[str | None] = mapped_column(String(180), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remote_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(80), nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    date_posted: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    skills: Mapped[list[JobSkill]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
    match_results: Mapped[list[MatchResult]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class JobSkill(Base):
    __tablename__ = "job_skills"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(120), index=True)
    normalized_skill_name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    importance: Mapped[str | None] = mapped_column(String(80), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    job: Mapped[JobPosting] = relationship(back_populates="skills")
