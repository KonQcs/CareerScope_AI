from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class JobPostingBase(BaseModel):
    external_id: str | None = Field(default=None, max_length=150)
    title: str = Field(min_length=2, max_length=180)
    company: str = Field(min_length=2, max_length=180)
    field: str | None = Field(default=None, max_length=100)
    job_family: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=180)
    country: str | None = Field(default=None, max_length=100)
    remote_type: str | None = Field(default=None, max_length=80)
    seniority: str | None = Field(default=None, max_length=80)
    salary_min: float | None = None
    salary_max: float | None = None
    description: str | None = None
    requirements_text: str | None = None
    source: str | None = Field(default=None, max_length=120)
    source_url: str | None = Field(default=None, max_length=500)
    date_posted: date | None = None


class JobPostingCreate(JobPostingBase):
    pass


class JobSkillRead(BaseModel):
    id: int
    job_id: int
    skill_name: str
    normalized_skill_name: str
    category: str | None = None
    importance: str | None = None
    evidence_text: str | None = None

    model_config = ConfigDict(from_attributes=True)


class JobPostingRead(JobPostingBase):
    id: int
    created_at: datetime
    skills: list[JobSkillRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
