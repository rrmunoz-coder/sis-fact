from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sisfact import create_app
from sisfact.db import connection


def main():
    app = create_app()
    with app.app_context():
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT USER, SYSDATE FROM DUAL")
                user, dt = cur.fetchone()
                print(f"ORACLE_OK user={user} database_datetime={dt}")


if __name__ == "__main__":
    main()
