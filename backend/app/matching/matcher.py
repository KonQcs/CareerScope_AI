from dataclasses import dataclass, field


@dataclass(frozen=True)
class MatchSummary:
    matching_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    weakly_evidenced_skills: list[str] = field(default_factory=list)
    explanation: str = "Matching logic has not been implemented yet."


def compare_profile_to_role(
    candidate_skills: list[str],
    role_requirements: list[str],
) -> MatchSummary:
    """Placeholder for explainable candidate-to-role matching."""
    _ = candidate_skills, role_requirements
    return MatchSummary()
