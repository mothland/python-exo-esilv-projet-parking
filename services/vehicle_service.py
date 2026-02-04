from database import get_connection


class VehicleError(Exception):
    pass


VALID_STATUTS = {
    "disponible",
    "en_sortie",
    "en_maintenance",
    "immobilise",
    "en_panne",
}

VALID_AFFECTATIONS = {
    "mutualise",
    "fonction",
}


def create_vehicle(
    immatriculation: str,
    marque: str,
    modele: str,
    type_vehicule: str,
    type_affectation: str,
    statut: str = "disponible",
    annee: int | None = None,
    date_acquisition: str | None = None,
    kilometrage_actuel: int = 0,
    carburant: str | None = None,
    puissance_fiscale: int | None = None,
    service_principal: str | None = None,
    seuil_revision_km: int | None = None,
    photo_path: str | None = None,
    db_path="db/parc_auto.db",
):
    if not immatriculation or not marque or not modele or not type_vehicule:
        raise VehicleError("Champs véhicule obligatoires manquants")

    if type_affectation not in VALID_AFFECTATIONS:
        raise VehicleError("Type d'affectation invalide")

    if statut not in VALID_STATUTS:
        raise VehicleError("Statut du véhicule invalide")

    try:
        with get_connection(db_path) as conn:
            conn.execute(
                """
                INSERT INTO vehicules (
                    immatriculation, marque, modele, type_vehicule,
                    annee, date_acquisition, kilometrage_actuel,
                    carburant, puissance_fiscale,
                    photo_path, type_affectation, statut,
                    service_principal, seuil_revision_km
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    immatriculation,
                    marque,
                    modele,
                    type_vehicule,
                    annee,
                    date_acquisition,
                    kilometrage_actuel,
                    carburant,
                    puissance_fiscale,
                    photo_path,
                    type_affectation,
                    statut,
                    service_principal,
                    seuil_revision_km,
                ),
            )
            conn.commit()
    except Exception as e:
        raise VehicleError(str(e))


def update_vehicle_status(
    vehicule_id: int,
    new_statut: str,
    db_path="db/parc_auto.db",
):
    if new_statut not in VALID_STATUTS:
        raise VehicleError("Statut invalide")

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE vehicules
            SET statut = ?
            WHERE id = ?
            """,
            (new_statut, vehicule_id),
        )
        if cur.rowcount == 0:
            raise VehicleError("Véhicule introuvable")
        conn.commit()


def get_vehicles(
    statut: str | None = None,
    type_affectation: str | None = None,
    db_path="db/parc_auto.db",
):
    query = "SELECT * FROM vehicules WHERE 1=1"
    params = []

    if statut:
        query += " AND statut = ?"
        params.append(statut)

    if type_affectation:
        query += " AND type_affectation = ?"
        params.append(type_affectation)

    query += " ORDER BY marque, modele"

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

def get_available_vehicles(db_path="db/parc_auto.db"):
    """
    Return only vehicles with statut = 'disponible'.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM vehicules
            WHERE statut = 'disponible'
            ORDER BY immatriculation
            """
        )
        return cur.fetchall()
