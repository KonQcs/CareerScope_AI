from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CandidateProfileBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=3, max_length=255)
    target_field: str = Field(min_length=2, max_length=100)
    target_job_title: str = Field(min_length=2, max_length=150)
    seniority_preference: str | None = Field(default=None, max_length=80)
    location_preference: str | None = Field(default=None, max_length=150)
    remote_preference: str | None = Field(default=None, max_length=80)


class CandidateProfileCreate(CandidateProfileBase):
    pass


class CandidateSkillRead(BaseModel):
    id: int
    candidate_id: int
    skill_name: str
    normalized_skill_name: str
    category: str | None = None
    evidence_source: str | None = None
    evidence_text: str | None = None
    evidence_strength: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateProjectRead(BaseModel):
    id: int
    candidate_id: int
    project_name: str
    source_url: str | None = None
    description: str | None = None
    detected_skills: list[str] = Field(default_factory=list)
    evidence_strength: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateProfileRead(CandidateProfileBase):
    id: int
    created_at: datetime
    skills: list[CandidateSkillRead] = Field(default_factory=list)
    projects: list[CandidateProjectRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CandidateAnalysisPreview(BaseModel):
    career_field: str
    desired_job_title: str
    cv_filename: str | None = None
    portfolio_links: list[str] = Field(default_factory=list)
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weakly_evidenced_skills: list[str] = Field(default_factory=list)
    recommended_jobs: list[str] = Field(default_factory=list)
    explanation: str
