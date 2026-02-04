from datetime import datetime
from database import get_connection


def log_action(
    action: str,
    user_id: int | None = None,
    details: str | None = None,
    db_path="db/parc_auto.db",
):
    if not action:
        raise ValueError("Action obligatoire")

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO logs (
                user_id, action, date_action, details
            ) VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                action,
                datetime.now().isoformat(timespec="seconds"),
                details,
            ),
        )
        conn.commit()


def get_logs(
    limit: int = 100,
    db_path="db/parc_auto.db",
):
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM logs
            ORDER BY date_action DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()
