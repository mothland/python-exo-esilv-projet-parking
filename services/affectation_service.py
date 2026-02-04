from database import get_connection


class AffectationError(Exception):
    pass


def create_affectation(
    vehicule_id: int,
    employe_id: int,
    date_debut: str,
    date_fin: str | None = None,
    db_path="db/parc_auto.db",
):
    """
    Create a permanent assignment between a vehicle and an employee.
    """
    if not vehicule_id or not employe_id or not date_debut:
        raise AffectationError("vehicule_id, employe_id et date_debut requis")

    with get_connection(db_path) as conn:
        cur = conn.cursor()

        # Ensure vehicle exists
        cur.execute(
            "SELECT id FROM vehicules WHERE id = ?",
            (vehicule_id,),
        )
        if cur.fetchone() is None:
            raise AffectationError("Véhicule introuvable")

        # Ensure employee exists
        cur.execute(
            "SELECT id FROM employes WHERE id = ?",
            (employe_id,),
        )
        if cur.fetchone() is None:
            raise AffectationError("Employé introuvable")

        cur.execute(
            """
            INSERT INTO affectations_permanentes (
                vehicule_id, employe_id, date_debut, date_fin
            ) VALUES (?, ?, ?, ?)
            """,
            (vehicule_id, employe_id, date_debut, date_fin),
        )

        conn.commit()


def get_active_affectation(
    vehicule_id: int,
    db_path="db/parc_auto.db",
):
    """
    Return the active (date_fin IS NULL) affectation for a vehicle.
    """
    with get_connection(db_path) as conn:
        return conn.execute(
            """
            SELECT *
            FROM affectations_permanentes
            WHERE vehicule_id = ?
              AND date_fin IS NULL
            """,
            (vehicule_id,),
        ).fetchone()


def end_affectation(
    affectation_id: int,
    date_fin: str,
    db_path="db/parc_auto.db",
):
    """
    End an affectation by setting date_fin.
    """
    if not affectation_id or not date_fin:
        raise AffectationError("affectation_id et date_fin requis")

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE affectations_permanentes
            SET date_fin = ?
            WHERE id = ?
            """,
            (date_fin, affectation_id),
        )

        if cur.rowcount == 0:
            raise AffectationError("Affectation introuvable")

        conn.commit()
