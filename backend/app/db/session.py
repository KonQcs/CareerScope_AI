from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def engine_kwargs_for_url(database_url: str) -> dict[str, object]:
    url = make_url(database_url)
    kwargs: dict[str, object] = {"pool_pre_ping": True}
    if _is_sqlite_url(url):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


def ensure_sqlite_directory(database_url: str) -> None:
    url = make_url(database_url)
    if not _is_sqlite_url(url) or not url.database or url.database == ":memory:":
        return

    database_path = Path(url.database)
    if database_path.parent != Path("."):
        database_path.parent.mkdir(parents=True, exist_ok=True)


def _is_sqlite_url(url: URL) -> bool:
    return url.drivername.startswith("sqlite")


database_url = normalize_database_url(settings.database_url)
ensure_sqlite_directory(database_url)
engine = create_engine(
    database_url,
    **engine_kwargs_for_url(database_url),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
