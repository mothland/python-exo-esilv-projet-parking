from datetime import date, timedelta
from database import get_connection


# =========================================================
# ALERTES DOCUMENTS (RETARD + PROCHE)
# =========================================================
def get_document_alerts(days_ahead=30, db_path="db/parc_auto.db"):
    today = date.today()
    limit_date = today + timedelta(days=days_ahead)

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                d.type_document,
                d.date_echeance,
                v.immatriculation
            FROM documents d
            JOIN vehicules v ON d.vehicule_id = v.id
            WHERE d.date_echeance IS NOT NULL
            ORDER BY d.date_echeance
        """)
        rows = cur.fetchall()

    alerts = []

    for r in rows:
        echeance = date.fromisoformat(r["date_echeance"])

        if echeance < today:
            statut = "retard"
        elif echeance <= limit_date:
            statut = "proche"
        else:
            continue  # pas une alerte

        alerts.append({
            "type": "Document",
            "vehicule": r["immatriculation"],
            "libelle": r["type_document"],
            "date_echeance": r["date_echeance"],
            "statut": statut,
        })

    return alerts


# =========================================================
# ALERTES MAINTENANCE (RETARD + PROCHE)
# =========================================================
def get_maintenance_alerts(days_ahead=30, db_path="db/parc_auto.db"):
    today = date.today()
    limit_date = today + timedelta(days=days_ahead)

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                m.type_intervention,
                m.date_prochaine_echeance,
                v.immatriculation
            FROM maintenances m
            JOIN vehicules v ON m.vehicule_id = v.id
            WHERE m.date_prochaine_echeance IS NOT NULL
            ORDER BY m.date_prochaine_echeance
        """)
        rows = cur.fetchall()

    alerts = []

    for r in rows:
        echeance = date.fromisoformat(r["date_prochaine_echeance"])

        if echeance < today:
            statut = "retard"
        elif echeance <= limit_date:
            statut = "proche"
        else:
            continue

        alerts.append({
            "type": "Maintenance",
            "vehicule": r["immatriculation"],
            "libelle": r["type_intervention"],
            "date_echeance": r["date_prochaine_echeance"],
            "statut": statut,
        })

    return alerts
