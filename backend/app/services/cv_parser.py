import re
from pathlib import Path
from typing import Any

from backend.app.skill_extraction.taxonomy import find_skills_in_text

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SECTION_HEADERS = {
    "education": ("education", "academic background"),
    "projects": ("projects", "project experience", "selected projects", "portfolio"),
    "work_experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment history",
    ),
    "certifications": ("certifications", "certificates", "licenses", "credentials"),
}
ALL_SECTION_HEADERS = {
    alias
    for aliases in SECTION_HEADERS.values()
    for alias in aliases
} | {"skills", "technical skills", "summary", "profile", "contact"}
MAX_SNIPPETS_PER_SECTION = 4


def extract_text_from_pdf(file_path: str) -> str:
    path = _resolve_existing_file(file_path)

    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PDF parsing requires PyMuPDF. Install project dependencies with "
            "`python -m pip install -r requirements.txt`."
        ) from exc

    text_parts: list[str] = []
    with fitz.open(str(path)) as document:
        for page in document:
            text_parts.append(page.get_text())
    return "\n".join(text_parts).strip()


def extract_text_from_txt(file_path: str) -> str:
    path = _resolve_existing_file(file_path)
    return path.read_text(encoding="utf-8", errors="replace").strip()


def extract_cv_text(file_path: str) -> str:
    path = _resolve_existing_file(file_path)
    suffix = path.suffix.casefold()

    if suffix == ".pdf":
        return extract_text_from_pdf(str(path))
    if suffix in {".txt", ".text"}:
        return extract_text_from_txt(str(path))
    if suffix == ".docx":
        return _extract_text_from_docx(path)

    raise ValueError(f"Unsupported CV file type: {path.suffix or '<none>'}. Use PDF or TXT.")


def parse_candidate_profile_from_text(text: str) -> dict[str, Any]:
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return _empty_profile()

    return {
        "probable_name": _extract_probable_name(normalized_text),
        "probable_email": _extract_probable_email(normalized_text),
        "skills": find_skills_in_text(normalized_text),
        "education_snippets": _extract_section_snippets(normalized_text, "education"),
        "project_snippets": _extract_section_snippets(normalized_text, "projects"),
        "work_experience_snippets": _extract_section_snippets(normalized_text, "work_experience"),
        "certifications": _extract_section_snippets(normalized_text, "certifications"),
    }


def extract_candidate_skills_from_cv(
    text: str,
    target_field: str | None = None,
) -> list[dict[str, str]]:
    return find_skills_in_text(text, field=target_field)


def _resolve_existing_file(file_path: str) -> Path:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"CV file not found: {file_path}")
    return path


def _extract_text_from_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError(
            "DOCX parsing requires python-docx. Install it to parse DOCX CV files."
        ) from exc

    document = Document(path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()


def _empty_profile() -> dict[str, Any]:
    return {
        "probable_name": None,
        "probable_email": None,
        "skills": [],
        "education_snippets": [],
        "project_snippets": [],
        "work_experience_snippets": [],
        "certifications": [],
    }


def _normalize_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _extract_probable_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def _extract_probable_name(text: str) -> str | None:
    for line in text.splitlines()[:8]:
        if _line_is_probable_name(line):
            return line.strip()
    return None


def _line_is_probable_name(line: str) -> bool:
    cleaned_line = line.strip()
    if not cleaned_line:
        return False
    if "@" in cleaned_line or "http" in cleaned_line.casefold():
        return False
    if _is_section_header(cleaned_line):
        return False
    if re.search(r"\d", cleaned_line):
        return False

    words = cleaned_line.split()
    if not 2 <= len(words) <= 5:
        return False
    return all(re.fullmatch(r"[A-Za-z][A-Za-z.'-]*", word) for word in words)


def _extract_section_snippets(text: str, section_key: str) -> list[str]:
    target_headers = SECTION_HEADERS[section_key]
    lines = text.splitlines()
    snippets: list[str] = []
    collecting = False
    buffer: list[str] = []

    for line in lines:
        header = _normalized_header(line)
        if header in target_headers:
            if buffer:
                snippets.extend(_buffer_to_snippets(buffer))
                buffer = []
            collecting = True
            continue

        if collecting and header in ALL_SECTION_HEADERS:
            snippets.extend(_buffer_to_snippets(buffer))
            buffer = []
            collecting = False
            continue

        if collecting:
            buffer.append(line)

    if collecting and buffer:
        snippets.extend(_buffer_to_snippets(buffer))

    return snippets[:MAX_SNIPPETS_PER_SECTION]


def _buffer_to_snippets(lines: list[str]) -> list[str]:
    snippets: list[str] = []
    current: list[str] = []

    for line in lines:
        cleaned_line = line.strip(" -\t\u2022")
        if not cleaned_line:
            continue
        if _looks_like_list_item(line) and current:
            snippets.append(_compact_snippet(current))
            current = [cleaned_line]
        else:
            current.append(cleaned_line)

    if current:
        snippets.append(_compact_snippet(current))

    return [snippet for snippet in snippets if snippet]


def _compact_snippet(lines: list[str]) -> str:
    snippet = re.sub(r"\s+", " ", " ".join(lines)).strip()
    return snippet[:400]


def _looks_like_list_item(line: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*\u2022]|\d+[.)])\s+", line))


def _normalized_header(line: str) -> str:
    return re.sub(r"[:\s]+$", "", line.strip().casefold())


def _is_section_header(line: str) -> bool:
    return _normalized_header(line) in ALL_SECTION_HEADERS
