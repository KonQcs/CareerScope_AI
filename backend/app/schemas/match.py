from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MatchResultRead(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    overall_score: float
    required_skill_score: float | None = None
    preferred_skill_score: float | None = None
    seniority_score: float | None = None
    domain_score: float | None = None
    portfolio_evidence_score: float | None = None
    location_score: float | None = None
    explanation: str | None = None
    missing_skills: list[str] = Field(default_factory=list)
    matching_skills: list[str] = Field(default_factory=list)
    weak_skills: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillGapReport(BaseModel):
    candidate_id: int
    job_id: int | None = None
    target_job_title: str
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weak_skills: list[str] = Field(default_factory=list)
    summary: str


class JobRecommendation(BaseModel):
    job_id: int
    title: str
    company: str
    overall_score: float
    match_label: str
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weak_skills: list[str] = Field(default_factory=list)
    explanation: str
