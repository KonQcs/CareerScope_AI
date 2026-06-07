import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.cv_parser import (  # noqa: E402
    extract_candidate_skills_from_cv,
    extract_cv_text,
    parse_candidate_profile_from_text,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a CV and print deterministic MVP signals.")
    parser.add_argument("file_path", help="Path to a PDF, TXT, or optional DOCX CV file.")
    parser.add_argument("--field", default=None, help="Optional target field for skill filtering.")
    args = parser.parse_args()

    text = extract_cv_text(args.file_path)
    profile = parse_candidate_profile_from_text(text)
    skills = extract_candidate_skills_from_cv(text, target_field=args.field)

    print(f"Extracted email: {profile['probable_email'] or 'Not found'}")
    print("Detected skills:")
    if skills:
        for skill in skills:
            print(f"- {skill['normalized_skill']} ({skill['category']})")
    else:
        print("- None detected")

    print("Possible project snippets:")
    _print_snippets(profile["project_snippets"])

    print("Possible education snippets:")
    _print_snippets(profile["education_snippets"])


def _print_snippets(snippets: list[str]) -> None:
    if not snippets:
        print("- None detected")
        return
    for snippet in snippets:
        print(f"- {snippet}")


if __name__ == "__main__":
    main()
