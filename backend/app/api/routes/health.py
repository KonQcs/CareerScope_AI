from fastapi import APIRouter

router = APIRouter(tags=["health"])

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
