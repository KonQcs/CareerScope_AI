from typing import Any

from backend.app.matching.scoring import read_value


def generate_match_explanation(
    candidate_profile: Any,
    job: Any,
    matching_skills: list[str],
    missing_skills: list[str],
    weak_skills: list[str],
    component_scores: dict[str, float],
) -> str:
    title = read_value(job, "title", "this role")
    company = read_value(job, "company", "the company")
    target_title = read_value(candidate_profile, "target_job_title", "the target role")

    parts = [
        f"{title} at {company} was compared with the candidate's target role: {target_title}."
    ]

    if matching_skills:
        parts.append(f"Matching skills: {_format_skill_list(matching_skills)}.")
    else:
        parts.append("No direct skill matches were found.")

    if missing_skills:
        parts.append(f"Missing skills: {_format_skill_list(missing_skills)}.")
    else:
        parts.append("No required skills appear to be missing.")

    if weak_skills:
        parts.append(f"Weakly evidenced skills: {_format_skill_list(weak_skills)}.")

    strongest_component = _best_component(component_scores)
    weakest_component = _worst_component(component_scores)
    if strongest_component:
        parts.append(
            f"Strongest signal: {strongest_component[0]} scored {strongest_component[1]:.0f}/100."
        )
    if weakest_component:
        parts.append(
            f"Weakest signal: {weakest_component[0]} scored {weakest_component[1]:.0f}/100."
        )

    return " ".join(parts)


def _format_skill_list(skills: list[str], limit: int = 8) -> str:
    visible_skills = skills[:limit]
    suffix = "" if len(skills) <= limit else f", and {len(skills) - limit} more"
    return ", ".join(visible_skills) + suffix


def _best_component(component_scores: dict[str, float]) -> tuple[str, float] | None:
    if not component_scores:
        return None
    return max(component_scores.items(), key=lambda item: item[1])


def _worst_component(component_scores: dict[str, float]) -> tuple[str, float] | None:
    if not component_scores:
        return None
    return min(component_scores.items(), key=lambda item: item[1])
