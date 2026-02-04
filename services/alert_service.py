from datetime import date, timedelta
from database import get_connection


def get_document_alerts(
    days_ahead: int = 30,
    db_path="db/parc_auto.db",
):
    """
    Documents expiring soon or already expired.
    """
    limit_date = (date.today() + timedelta(days=days_ahead)).isoformat()

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT d.*, v.immatriculation
            FROM documents d
            JOIN vehicules v ON d.vehicule_id = v.id
            WHERE d.date_echeance IS NOT NULL
              AND d.date_echeance <= ?
            ORDER BY d.date_echeance
            """,
            (limit_date,),
        )
        return cur.fetchall()


def get_maintenance_alerts(
    db_path="db/parc_auto.db",
):
    """
    Maintenance with next due date reached or passed.
    """
    today = date.today().isoformat()

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.*, v.immatriculation
            FROM maintenances m
            JOIN vehicules v ON m.vehicule_id = v.id
            WHERE m.date_prochaine_echeance IS NOT NULL
              AND m.date_prochaine_echeance <= ?
            ORDER BY m.date_prochaine_echeance
            """,
            (today,),
        )
        return cur.fetchall()


def get_revision_km_alerts(
    db_path="db/parc_auto.db",
):
    """
    Vehicles exceeding revision kilometer threshold.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM vehicules
            WHERE seuil_revision_km IS NOT NULL
              AND kilometrage_actuel >= seuil_revision_km
            ORDER BY kilometrage_actuel DESC
            """
        )
        return cur.fetchall()
