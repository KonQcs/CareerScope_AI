from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MatchResultRead(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    overall_score: float
    explainable_score: float | None = None
    semantic_similarity_score: float | None = None
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
    target_field: str
    target_job_title: str
    overall_readiness_score: float
    matching_skills: list[str] = Field(default_factory=list)
    strong_skills: list[str] = Field(default_factory=list)
    partial_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    portfolio_evidenced_skills: list[str] = Field(default_factory=list)
    cv_only_skills: list[str] = Field(default_factory=list)
    recommended_projects: list[str] = Field(default_factory=list)
    recommended_learning_topics: list[str] = Field(default_factory=list)
    explanation: str


class JobRecommendation(BaseModel):
    job_id: int
    title: str
    company: str
    location: str | None = None
    overall_score: float
    explainable_score: float | None = None
    semantic_similarity_score: float | None = None
    match_label: str
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weak_skills: list[str] = Field(default_factory=list)
    explanation: str


class SkillGapRequest(BaseModel):
    target_field: str = Field(min_length=2, max_length=100)
    target_job_title: str = Field(min_length=2, max_length=150)


class JobRecommendationRequest(SkillGapRequest):
    limit: int = Field(default=10, ge=1, le=50)
