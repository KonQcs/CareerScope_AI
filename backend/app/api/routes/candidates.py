import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.session import get_db
from backend.app.models.candidate import CandidateProfile, CandidateSkill
from backend.app.schemas.candidate import CandidateProfileCreate, CandidateProfileRead
from backend.app.services.cv_parser import (
    extract_candidate_skills_from_cv,
    extract_cv_text,
    parse_candidate_profile_from_text,
)
from backend.app.services.data_quality import (
    normalize_evidence_source,
    validate_candidate_profile,
    validate_candidate_skill,
)

router = APIRouter(prefix="/candidates", tags=["candidates"])
UPLOAD_DIR = Path(__file__).resolve().parents[4] / "data" / "raw" / "uploads"
ALLOWED_CV_SUFFIXES = {".pdf", ".txt", ".text", ".docx"}


@router.post("", response_model=CandidateProfileRead, status_code=status.HTTP_201_CREATED)
def create_candidate(
    candidate_data: CandidateProfileCreate,
    session: Session = Depends(get_db),
) -> CandidateProfile:
    quality_issues = validate_candidate_profile(candidate_data.model_dump())
    if quality_issues:
        raise HTTPException(
            status_code=422,
            detail=quality_issues,
        )

    existing_candidate = session.scalar(
        select(CandidateProfile).where(CandidateProfile.email == candidate_data.email)
    )
    if existing_candidate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A candidate with this email already exists.",
        )

    candidate = CandidateProfile(**candidate_data.model_dump())
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


@router.get("/{candidate_id}", response_model=CandidateProfileRead)
def read_candidate(
    candidate_id: int,
    session: Session = Depends(get_db),
) -> CandidateProfile:
    return _get_candidate(session, candidate_id)


@router.post("/{candidate_id}/cv")
async def upload_candidate_cv(
    candidate_id: int,
    cv: UploadFile = File(...),
    session: Session = Depends(get_db),
) -> dict[str, object]:
    candidate = _get_candidate(session, candidate_id)
    upload_path = await _save_upload(candidate_id, cv)

    try:
        cv_text = extract_cv_text(str(upload_path))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    parsed_profile = parse_candidate_profile_from_text(cv_text)
    extracted_skills = extract_candidate_skills_from_cv(
        cv_text,
        target_field=candidate.target_field,
    )

    session.execute(
        delete(CandidateSkill).where(
            CandidateSkill.candidate_id == candidate.id,
            CandidateSkill.evidence_source.in_(("cv", "CV")),
        )
    )
    for skill in extracted_skills:
        skill_record = {
            "candidate_id": candidate.id,
            "skill_name": skill["skill"],
            "normalized_skill_name": skill["normalized_skill"],
            "category": skill.get("category"),
            "evidence_source": normalize_evidence_source("CV"),
            "evidence_text": skill.get("evidence_snippet"),
            "evidence_strength": 0.65,
        }
        quality_issues = validate_candidate_skill(skill_record)
        if quality_issues:
            raise HTTPException(
                status_code=422,
                detail=quality_issues,
            )
        session.add(
            CandidateSkill(
                **skill_record,
            )
        )
    session.commit()

    return {
        "candidate_id": candidate.id,
        "filename": cv.filename,
        "probable_email": parsed_profile["probable_email"],
        "probable_name": parsed_profile["probable_name"],
        "skills": extracted_skills,
        "stored_skill_count": len(extracted_skills),
    }


def _get_candidate(session: Session, candidate_id: int) -> CandidateProfile:
    candidate = session.scalar(
        select(CandidateProfile)
        .options(
            selectinload(CandidateProfile.skills),
            selectinload(CandidateProfile.projects),
        )
        .where(CandidateProfile.id == candidate_id)
    )
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} was not found.",
        )
    return candidate


async def _save_upload(candidate_id: int, upload: UploadFile) -> Path:
    filename = upload.filename or "uploaded_cv"
    suffix = Path(filename).suffix.casefold()
    if suffix not in ALLOWED_CV_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported CV file type. Upload a PDF, TXT, or DOCX file.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(filename)
    destination = UPLOAD_DIR / f"candidate_{candidate_id}_{safe_name}"

    with destination.open("wb") as output_file:
        while chunk := await upload.read(1024 * 1024):
            output_file.write(chunk)

    return destination


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)
