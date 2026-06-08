from sqlalchemy import inspect, text

from backend.app import models as _models  # noqa: F401
from backend.app.db.base import Base
from backend.app.db.session import engine

SQLITE_ADDITIVE_COLUMNS = {
    "job_postings": {
        "field": "VARCHAR(100)",
        "job_family": "VARCHAR(120)",
    },
    "match_results": {
        "explainable_score": "FLOAT",
        "semantic_similarity_score": "FLOAT",
    },
}


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    sync_sqlite_schema(engine)


def sync_sqlite_schema(bind) -> None:
    if bind.dialect.name != "sqlite":
        return

    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())
    with bind.begin() as connection:
        for table_name, columns in SQLITE_ADDITIVE_COLUMNS.items():
            if table_name not in table_names:
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_type in columns.items():
                if column_name in existing_columns:
                    continue
                connection.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                )
