from __future__ import annotations

import math
import re
from functools import lru_cache
from typing import Any

from backend.app.matching.scoring import read_value, skill_name

DEFAULT_SENTENCE_TRANSFORMER_MODEL = "all-MiniLM-L6-v2"
_EMBEDDING_CACHE: dict[str, list[float]] = {}
_SIMILARITY_CACHE: dict[tuple[str, str], float] = {}


def compute_text_similarity(text_a: str, text_b: str) -> float:
    normalized_a = _normalize_text(text_a)
    normalized_b = _normalize_text(text_b)
    if not normalized_a or not normalized_b:
        return 0.0
    if normalized_a == normalized_b:
        return 100.0

    cache_key = _similarity_cache_key(normalized_a, normalized_b)
    if cache_key in _SIMILARITY_CACHE:
        return _SIMILARITY_CACHE[cache_key]

    sentence_transformer_score = _sentence_transformer_similarity(normalized_a, normalized_b)
    if sentence_transformer_score is not None:
        _SIMILARITY_CACHE[cache_key] = sentence_transformer_score
        return sentence_transformer_score

    tfidf_score = _tfidf_similarity(normalized_a, normalized_b)
    _SIMILARITY_CACHE[cache_key] = tfidf_score
    return tfidf_score


def rank_jobs_by_semantic_similarity(
    candidate_text: str,
    jobs: list[dict[str, Any]],
) -> list[tuple[Any, float]]:
    ranked_jobs: list[tuple[Any, float]] = []
    for job in jobs:
        job_id = (
            read_value(job, "id") or read_value(job, "job_id") or read_value(job, "external_id")
        )
        job_text = build_job_text(
            job,
            read_value(job, "skills", []) or read_value(job, "job_skills", []),
        )
        ranked_jobs.append((job_id, compute_text_similarity(candidate_text, job_text)))

    return sorted(ranked_jobs, key=lambda item: item[1], reverse=True)


def build_candidate_profile_text(
    candidate_profile: Any,
    skills: list[Any],
    projects: list[Any],
) -> str:
    parts = [
        read_value(candidate_profile, "target_field"),
        read_value(candidate_profile, "target_job_title"),
        read_value(candidate_profile, "seniority_preference"),
        read_value(candidate_profile, "location_preference"),
        read_value(candidate_profile, "remote_preference"),
    ]

    for skill in skills:
        parts.extend(
            [
                skill_name(skill),
                read_value(skill, "category"),
                read_value(skill, "evidence_source"),
                read_value(skill, "evidence_text"),
            ]
        )

    for project in projects:
        detected_skills = read_value(project, "detected_skills", []) or []
        parts.extend(
            [
                read_value(project, "project_name") or read_value(project, "name"),
                read_value(project, "description"),
                read_value(project, "evidence_text"),
                " ".join(str(skill) for skill in detected_skills),
            ]
        )

    return _normalize_text(" ".join(str(part) for part in parts if part))


def build_job_text(job: Any, job_skills: list[Any]) -> str:
    parts = [
        read_value(job, "title"),
        read_value(job, "company"),
        read_value(job, "location"),
        read_value(job, "country"),
        read_value(job, "remote_type"),
        read_value(job, "seniority"),
        read_value(job, "description"),
        read_value(job, "requirements_text"),
    ]

    for job_skill in job_skills:
        parts.extend(
            [
                skill_name(job_skill),
                read_value(job_skill, "category"),
                read_value(job_skill, "importance"),
                read_value(job_skill, "evidence_text"),
            ]
        )

    return _normalize_text(" ".join(str(part) for part in parts if part))


def clear_semantic_caches() -> None:
    _EMBEDDING_CACHE.clear()
    _SIMILARITY_CACHE.clear()


def _sentence_transformer_similarity(text_a: str, text_b: str) -> float | None:
    model = _get_sentence_transformer_model()
    if model is None:
        return None

    vector_a = _cached_sentence_embedding(model, text_a)
    vector_b = _cached_sentence_embedding(model, text_b)
    return _score_from_cosine(_cosine_similarity(vector_a, vector_b))


@lru_cache(maxsize=1)
def _get_sentence_transformer_model() -> Any | None:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None

    try:
        return SentenceTransformer(DEFAULT_SENTENCE_TRANSFORMER_MODEL, device="cpu")
    except Exception:
        return None


def _cached_sentence_embedding(model: Any, text: str) -> list[float]:
    if text not in _EMBEDDING_CACHE:
        embedding = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
        _EMBEDDING_CACHE[text] = [float(value) for value in embedding]
    return _EMBEDDING_CACHE[text]


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return _lexical_similarity(text_a, text_b)

    try:
        matrix = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform(
            [text_a, text_b]
        )
        similarity = float(cosine_similarity(matrix[0], matrix[1])[0][0])
    except ValueError:
        return _lexical_similarity(text_a, text_b)

    return _score_from_cosine(similarity)


def _lexical_similarity(text_a: str, text_b: str) -> float:
    tokens_a = set(_tokenize(text_a))
    tokens_b = set(_tokenize(text_b))
    if not tokens_a or not tokens_b:
        return 0.0
    return round(100 * len(tokens_a & tokens_b) / len(tokens_a | tokens_b), 2)


def _cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b:
        return 0.0

    dot_product = sum(left * right for left, right in zip(vector_a, vector_b, strict=False))
    magnitude_a = math.sqrt(sum(value * value for value in vector_a))
    magnitude_b = math.sqrt(sum(value * value for value in vector_b))
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def _score_from_cosine(value: float) -> float:
    return round(max(0.0, min(1.0, value)) * 100, 2)


def _normalize_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9+#.]+", text.casefold())


def _similarity_cache_key(text_a: str, text_b: str) -> tuple[str, str]:
    return tuple(sorted((text_a, text_b)))
