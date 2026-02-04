from database import get_connection


def get_fleet_summary(db_path="db/parc_auto.db"):
    """
    Return fleet summary counts.
    Contract intentionally stable.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM vehicules")
        total = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM vehicules WHERE statut = 'disponible'"
        )
        available = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM vehicules WHERE statut = 'en_sortie'"
        )
        en_sortie = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM vehicules WHERE statut = 'en_maintenance'"
        )
        maintenance = cur.fetchone()[0]

        # Optional extra states (DO NOT expose as official keys)
        cur.execute(
            "SELECT COUNT(*) FROM vehicules WHERE statut = 'en_panne'"
        )
        panne = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM vehicules WHERE statut = 'immobilise'"
        )
        immobilise = cur.fetchone()[0]

    return {
        "total": total,
        "available": available,
        "en_sortie": en_sortie,
        "maintenance": maintenance,

        # extra keys (non-breaking, optional consumers)
        "_panne": panne,
        "_immobilise": immobilise,

        "parc_complet": available == 0 and total > 0,
    }

def get_available_vehicles(db_path="db/parc_auto.db"):
    """
    Return list of available vehicles.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, immatriculation, marque, modele
            FROM vehicules
            WHERE statut = 'disponible'
            ORDER BY marque, modele
            """
        )
        return cur.fetchall()


def get_vehicle_type_counts(db_path="db/parc_auto.db"):
    """
    Return number of vehicles per type.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT type_vehicule, COUNT(*) AS count
            FROM vehicules
            GROUP BY type_vehicule
            """
        )
        rows = cur.fetchall()

    return {row["type_vehicule"]: row["count"] for row in rows}


def get_maintenance_costs_by_vehicle(db_path="db/parc_auto.db"):
    """
    Return total maintenance cost per vehicle.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                v.immatriculation,
                SUM(m.cout) AS total_cout
            FROM maintenances m
            JOIN vehicules v ON v.id = m.vehicule_id
            GROUP BY v.immatriculation
            HAVING total_cout IS NOT NULL
            ORDER BY total_cout DESC
            """
        )
        return cur.fetchall()
