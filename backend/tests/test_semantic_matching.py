from backend.app.matching import semantic


def test_identical_texts_produce_high_similarity() -> None:
    score = semantic.compute_text_similarity(
        "Python SQL Spark data engineering",
        "Python SQL Spark data engineering",
    )

    assert score == 100.0


def test_unrelated_texts_produce_lower_similarity(monkeypatch) -> None:
    monkeypatch.setattr(semantic, "_get_sentence_transformer_model", lambda: None)
    semantic.clear_semantic_caches()

    related_score = semantic.compute_text_similarity(
        "Python SQL Spark data pipeline",
        "Python SQL Spark ETL pipeline",
    )
    unrelated_score = semantic.compute_text_similarity(
        "Python SQL Spark data pipeline",
        "budgeting accounting valuation risk analysis",
    )

    assert related_score > unrelated_score


def test_tfidf_fallback_works_without_sentence_transformers(monkeypatch) -> None:
    monkeypatch.setattr(semantic, "_get_sentence_transformer_model", lambda: None)
    semantic.clear_semantic_caches()

    score = semantic.compute_text_similarity(
        "Airflow dbt PostgreSQL Docker data quality",
        "Docker PostgreSQL Airflow ELT project",
    )

    assert score > 0


def test_job_ranking_returns_sorted_results(monkeypatch) -> None:
    monkeypatch.setattr(semantic, "_get_sentence_transformer_model", lambda: None)
    semantic.clear_semantic_caches()

    ranked_jobs = semantic.rank_jobs_by_semantic_similarity(
        candidate_text="Data engineer with Python, SQL, Spark, and ETL pipeline experience.",
        jobs=[
            {
                "id": 1,
                "title": "Financial Analyst",
                "description": "Budgeting, valuation, accounting, and variance analysis.",
            },
            {
                "id": 2,
                "title": "Data Engineer",
                "description": "Build Python SQL Spark ETL pipelines for analytics teams.",
            },
            {
                "id": 3,
                "title": "Supply Chain Analyst",
                "description": "Inventory planning, route optimization, and ERP reporting.",
            },
        ],
    )

    scores = [score for _, score in ranked_jobs]
    assert ranked_jobs[0][0] == 2
    assert scores == sorted(scores, reverse=True)
