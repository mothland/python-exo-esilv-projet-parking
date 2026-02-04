from database import get_connection


class ReservationError(Exception):
    pass


def create_sortie(
    vehicule_id: int,
    employe_id: int,
    km_depart: int,
    motif: str,
    destination: str,
    date_sortie: str | None = None,
    db_path="db/parc_auto.db",
):
    if km_depart < 0:
        raise ReservationError("Kilométrage de départ invalide")

    with get_connection(db_path) as conn:
        cur = conn.cursor()

        # Check vehicle availability
        cur.execute(
            "SELECT statut FROM vehicules WHERE id = ?",
            (vehicule_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ReservationError("Véhicule introuvable")
        if row["statut"] != "disponible":
            raise ReservationError("Véhicule non disponible")

        # Check employee authorization
        cur.execute(
            """
            SELECT autorise_conduire
            FROM employes
            WHERE id = ?
            """,
            (employe_id,),
        )
        emp = cur.fetchone()
        if not emp or not emp["autorise_conduire"]:
            raise ReservationError("Employé non autorisé à conduire")

        # Create sortie
        cur.execute(
            """
            INSERT INTO sorties_reservations (
                vehicule_id, employe_id,
                km_depart, motif, destination,
                statut
            ) VALUES (?, ?, ?, ?, ?, 'en_cours')
            """,
            (
                vehicule_id,
                employe_id,
                km_depart,
                motif,
                destination,
            ),
        )

        # Update vehicle status
        cur.execute(
            """
            UPDATE vehicules
            SET statut = 'en_sortie'
            WHERE id = ?
            """,
            (vehicule_id,),
        )

        conn.commit()


def return_vehicle(
    sortie_id: int,
    km_retour: int,
    etat_retour: str | None = None,
    statut_vehicule_apres: str = "disponible",
    db_path="db/parc_auto.db",
):
    with get_connection(db_path) as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT vehicule_id, km_depart
            FROM sorties_reservations
            WHERE id = ? AND statut = 'en_cours'
            """,
            (sortie_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ReservationError("Sortie introuvable ou déjà clôturée")

        if km_retour < row["km_depart"]:
            raise ReservationError("Kilométrage retour invalide")

        vehicule_id = row["vehicule_id"]

        # Close sortie
        cur.execute(
            """
            UPDATE sorties_reservations
            SET km_retour = ?, etat_retour = ?, statut = 'terminee'
            WHERE id = ?
            """,
            (km_retour, etat_retour, sortie_id),
        )

        # Update vehicle kilometrage & status
        cur.execute(
            """
            UPDATE vehicules
            SET kilometrage_actuel = ?, statut = ?
            WHERE id = ?
            """,
            (km_retour, statut_vehicule_apres, vehicule_id),
        )

        conn.commit()

def create_reservation(
    vehicule_id: int,
    employe_id: int,
    date_sortie: str,
    date_retour_prevue: str | None = None,
    db_path="db/parc_auto.db",
):
    """
    UI-facing alias for create_sortie.
    """
    return create_sortie(
        vehicule_id=vehicule_id,
        employe_id=employe_id,
        km_depart=0,
        motif="Reservation",
        destination="",
        date_sortie=date_sortie,
        db_path=db_path,
    )


def get_all_reservations(db_path="db/parc_auto.db"):
    """
    Return all reservations / sorties with vehicle & employee info.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                s.id,
                s.statut,
                s.date_sortie_prevue,
                s.date_sortie_reelle,
                s.date_retour_prevue,
                s.date_retour_reelle,
                v.immatriculation,
                e.prenom,
                e.nom
            FROM sorties_reservations s
            JOIN vehicules v ON v.id = s.vehicule_id
            JOIN employes e ON e.id = s.employe_id
            ORDER BY s.id DESC
            """
        )
        return cur.fetchall()
