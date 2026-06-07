from fastapi import APIRouter, File, Form, UploadFile

from backend.app.schemas.candidate import CandidateAnalysisPreview
from backend.app.services.candidate_analysis import build_analysis_preview

router = APIRouter()

CAREER_FIELDS = [
    "Computer Science",
    "Logistics",
    "Finance",
    "Marketing",
    "Healthcare",
    "Engineering",
]


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "CareerScope AI"}


@router.get("/career-fields", response_model=list[str])
def list_career_fields() -> list[str]:
    return CAREER_FIELDS


@router.post("/candidate/analyze", response_model=CandidateAnalysisPreview)
async def analyze_candidate(
    career_field: str = Form(...),
    desired_job_title: str = Form(...),
    portfolio_links: str = Form(default=""),
    cv: UploadFile = File(...),
) -> CandidateAnalysisPreview:
    links = [
        link.strip()
        for link in portfolio_links.replace("\n", ",").split(",")
        if link.strip()
    ]
    return build_analysis_preview(
        career_field=career_field,
        desired_job_title=desired_job_title,
        cv_filename=cv.filename,
        portfolio_links=links,
    )
