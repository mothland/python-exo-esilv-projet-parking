from database import get_connection


class MaintenanceError(Exception):
    pass


def record_maintenance(
    vehicule_id: int,
    date_: str,
    type_intervention: str,
    kilometrage: int | None = None,
    cout: float | None = None,
    prestataire: str | None = None,
    remarques: str | None = None,
    date_prochaine_echeance: str | None = None,
    db_path="db/parc_auto.db",
):
    if not date_ or not type_intervention:
        raise MaintenanceError("Date et type d'intervention requis")

    with get_connection(db_path) as conn:
        cur = conn.cursor()

        # Ensure vehicle exists
        cur.execute("SELECT id FROM vehicules WHERE id = ?", (vehicule_id,))
        if cur.fetchone() is None:
            raise MaintenanceError("Véhicule introuvable")

        cur.execute(
            """
            INSERT INTO maintenances (
                vehicule_id, date, type_intervention, kilometrage,
                cout, prestataire, remarques, date_prochaine_echeance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vehicule_id,
                date_,
                type_intervention,
                kilometrage,
                cout,
                prestataire,
                remarques,
                date_prochaine_echeance,
            ),
        )

        conn.commit()


def get_maintenances_for_vehicle(
    vehicule_id: int,
    db_path="db/parc_auto.db",
):
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM maintenances
            WHERE vehicule_id = ?
            ORDER BY date DESC
            """,
            (vehicule_id,),
        )
        return cur.fetchall()

def add_maintenance(
    vehicule_id: int,
    date: str,
    type_intervention: str,
    kilometrage: int | None = None,
    cout: float | None = None,
    prestataire: str | None = None,
    remarques: str | None = None,
    date_prochaine_echeance: str | None = None,
    db_path="db/parc_auto.db",
):
    """
    UI-facing helper for recording maintenance.
    """
    return record_maintenance(
        vehicule_id=vehicule_id,
        date_=date,
        type_intervention=type_intervention,
        kilometrage=kilometrage,
        cout=cout,
        prestataire=prestataire,
        remarques=remarques,
        date_prochaine_echeance=date_prochaine_echeance,
        db_path=db_path,
    )


def get_all_maintenances(db_path="db/parc_auto.db"):
    """
    Return all maintenances with vehicle info.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                m.date,
                m.type_intervention,
                m.kilometrage,
                m.cout,
                m.prestataire,
                m.date_prochaine_echeance,
                v.immatriculation
            FROM maintenances m
            JOIN vehicules v ON v.id = m.vehicule_id
            ORDER BY m.date DESC
            """
        )
        return cur.fetchall()
