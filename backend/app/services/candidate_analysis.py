from backend.app.schemas.candidate import CandidateAnalysisPreview


def build_analysis_preview(
    career_field: str,
    desired_job_title: str,
    cv_filename: str | None,
    portfolio_links: list[str],
) -> CandidateAnalysisPreview:
    return CandidateAnalysisPreview(
        career_field=career_field,
        desired_job_title=desired_job_title,
        cv_filename=cv_filename,
        portfolio_links=portfolio_links,
        explanation=(
            "Analysis pipeline placeholder. Future versions will parse the CV, inspect portfolio "
            "evidence, compare against target-role requirements, and explain job recommendations."
        ),
    )
