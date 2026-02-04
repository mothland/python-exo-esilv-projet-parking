from datetime import date, timedelta
from database import get_connection


class DocumentError(Exception):
    pass


def add_document(
    vehicule_id: int,
    type_document: str,
    chemin_fichier: str,
    date_echeance: str | None = None,
    date_emission: str | None = None,
    description: str | None = None,
    db_path="db/parc_auto.db",
):
    if not vehicule_id:
        raise DocumentError("Document doit être lié à un véhicule")

    if not type_document or not chemin_fichier:
        raise DocumentError("Type de document et fichier requis")

    with get_connection(db_path) as conn:
        cur = conn.cursor()

        # Check vehicle exists
        cur.execute(
            "SELECT id FROM vehicules WHERE id = ?",
            (vehicule_id,),
        )
        if cur.fetchone() is None:
            raise DocumentError("Véhicule introuvable")

        cur.execute(
            """
            INSERT INTO documents (
                vehicule_id,
                type_document,
                date_emission,
                date_echeance,
                chemin_fichier,
                description
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                vehicule_id,
                type_document,
                date_emission,
                date_echeance,
                chemin_fichier,
                description,
            ),
        )

        conn.commit()


def get_documents_for_vehicle(
    vehicule_id: int,
    db_path="db/parc_auto.db",
):
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM documents
            WHERE vehicule_id = ?
            ORDER BY date_echeance
            """,
            (vehicule_id,),
        )
        return cur.fetchall()


def get_expiring_documents(
    days_ahead: int = 30,
    db_path="db/parc_auto.db",
):
    """
    Return documents expiring within `days_ahead` days (including expired).
    """
    limit_date = (date.today() + timedelta(days=days_ahead)).isoformat()

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM documents
            WHERE date_echeance IS NOT NULL
              AND date_echeance <= ?
            ORDER BY date_echeance
            """,
            (limit_date,),
        )
        return cur.fetchall()
