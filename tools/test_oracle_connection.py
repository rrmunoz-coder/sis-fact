from sisfact import create_app
from sisfact.db import connection

app = create_app()

with app.app_context():
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT USER, SYSDATE FROM DUAL")
            user, dt = cur.fetchone()
            print(f"ORACLE_OK user={user} database_datetime={dt}")
