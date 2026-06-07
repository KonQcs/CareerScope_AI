from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.init_db import init_db  # noqa: E402
from backend.app.db.session import SessionLocal  # noqa: E402
from backend.app.job_collector.sample_loader import import_sample_jobs_to_db  # noqa: E402


def main() -> None:
    init_db()
    with SessionLocal() as session:
        inserted_count = import_sample_jobs_to_db(session)
    print(f"Inserted sample jobs: {inserted_count}")


if __name__ == "__main__":
    main()
