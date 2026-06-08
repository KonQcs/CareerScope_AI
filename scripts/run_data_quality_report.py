import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.init_db import init_db  # noqa: E402
from backend.app.db.session import SessionLocal  # noqa: E402
from backend.app.models.candidate import CandidateProfile, CandidateSkill  # noqa: E402
from backend.app.models.job import JobPosting, JobSkill  # noqa: E402
from backend.app.services.data_quality import (  # noqa: E402
    validate_candidate_profile,
    validate_candidate_skill,
    validate_job_posting,
    validate_job_skill,
)


def main() -> None:
    init_db()
    issues_by_entity: dict[str, list[str]] = defaultdict(list)

    with SessionLocal() as session:
        candidate_count = _count(session, CandidateProfile)
        job_count = _count(session, JobPosting)
        candidate_skill_count = _count(session, CandidateSkill)
        job_skill_count = _count(session, JobSkill)

        for candidate in session.scalars(select(CandidateProfile)).all():
            _collect_issues(
                issues_by_entity,
                "CandidateProfile",
                f"candidate_profiles#{candidate.id}",
                validate_candidate_profile(candidate),
            )

        for skill in session.scalars(select(CandidateSkill)).all():
            _collect_issues(
                issues_by_entity,
                "CandidateSkill",
                f"candidate_skills#{skill.id}",
                validate_candidate_skill(skill),
            )

        for job in session.scalars(
            select(JobPosting).options(selectinload(JobPosting.skills))
        ).all():
            _collect_issues(
                issues_by_entity,
                "JobPosting",
                f"job_postings#{job.id}",
                validate_job_posting(job),
            )

        for skill in session.scalars(select(JobSkill)).all():
            _collect_issues(
                issues_by_entity,
                "JobSkill",
                f"job_skills#{skill.id}",
                validate_job_skill(skill),
            )

    print("CareerScope AI Data Quality Report")
    print(f"Candidates: {candidate_count}")
    print(f"Jobs: {job_count}")
    print(
        f"Skills: {candidate_skill_count + job_skill_count} "
        f"({candidate_skill_count} candidate, {job_skill_count} job)"
    )

    if not issues_by_entity:
        print("Validation issues: none")
        return

    print("Validation issues:")
    for entity_name in sorted(issues_by_entity):
        print(f"\n{entity_name}")
        for issue in issues_by_entity[entity_name]:
            print(f"- {issue}")


def _count(session, model: type) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


def _collect_issues(
    issues_by_entity: dict[str, list[str]],
    entity_name: str,
    record_label: str,
    issues: list[str],
) -> None:
    for issue in issues:
        issues_by_entity[entity_name].append(f"{record_label}: {issue}")


if __name__ == "__main__":
    main()
