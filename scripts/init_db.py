import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings  # noqa: E402
from backend.app.db.init_db import init_db  # noqa: E402


def main() -> None:
    init_db()
    print(f"Database tables created for {settings.database_url}.")


if __name__ == "__main__":
    main()
