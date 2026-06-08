from pathlib import Path

from backend.app.db.session import (
    engine_kwargs_for_url,
    ensure_sqlite_directory,
    normalize_database_url,
)


def test_postgresql_url_is_normalized_to_psycopg_driver() -> None:
    assert (
        normalize_database_url("postgresql://user:pass@localhost:5432/careerscope")
        == "postgresql+psycopg://user:pass@localhost:5432/careerscope"
    )
    assert (
        normalize_database_url("postgres://user:pass@localhost:5432/careerscope")
        == "postgresql+psycopg://user:pass@localhost:5432/careerscope"
    )
    assert (
        normalize_database_url("postgresql+psycopg://user:pass@localhost:5432/careerscope")
        == "postgresql+psycopg://user:pass@localhost:5432/careerscope"
    )


def test_sqlite_engine_kwargs_include_thread_connect_args() -> None:
    kwargs = engine_kwargs_for_url("sqlite:///./data/careerscope.db")

    assert kwargs["connect_args"] == {"check_same_thread": False}
    assert kwargs["pool_pre_ping"] is True


def test_postgresql_engine_kwargs_do_not_include_sqlite_connect_args() -> None:
    kwargs = engine_kwargs_for_url("postgresql+psycopg://user:pass@localhost/db")

    assert "connect_args" not in kwargs
    assert kwargs["pool_pre_ping"] is True


def test_ensure_sqlite_directory_creates_parent(tmp_path: Path) -> None:
    database_path = tmp_path / "nested" / "careerscope.db"

    ensure_sqlite_directory(f"sqlite:///{database_path.as_posix()}")

    assert database_path.parent.is_dir()
