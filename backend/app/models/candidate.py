from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.match import MatchResult


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    target_field: Mapped[str] = mapped_column(String(100), index=True)
    target_job_title: Mapped[str] = mapped_column(String(150), index=True)
    seniority_preference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    location_preference: Mapped[str | None] = mapped_column(String(150), nullable=True)
    remote_preference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    skills: Mapped[list[CandidateSkill]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list[CandidateProject]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    match_results: Mapped[list[MatchResult]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(120), index=True)
    normalized_skill_name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evidence_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_strength: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    candidate: Mapped[CandidateProfile] = relationship(back_populates="skills")


class CandidateProject(Base):
    __tablename__ = "candidate_projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    project_name: Mapped[str] = mapped_column(String(180), index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_strength: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    candidate: Mapped[CandidateProfile] = relationship(back_populates="projects")
