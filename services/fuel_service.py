from database import get_connection


class FuelError(Exception):
    pass


# =========================================================
# ENREGISTRER UN RAVITAILLEMENT
# =========================================================
def record_fuel(
    vehicule_id: int,
    employe_id: int,
    date: str,
    quantite_litres: float,
    cout: float,
    kilometrage: int | None = None,
    station: str | None = None,
    db_path="db/parc_auto.db",
):
    if not date:
        raise FuelError("Date requise")

    if quantite_litres is None or quantite_litres <= 0:
        raise FuelError("Quantité invalide")

    if cout is None or cout < 0:
        raise FuelError("Coût invalide")

    if kilometrage is not None and kilometrage < 0:
        raise FuelError("Kilométrage invalide")

    with get_connection(db_path) as conn:
        cur = conn.cursor()

        # Vérifications
        cur.execute("SELECT id FROM vehicules WHERE id = ?", (vehicule_id,))
        if cur.fetchone() is None:
            raise FuelError("Véhicule introuvable")

        cur.execute("SELECT id FROM employes WHERE id = ?", (employe_id,))
        if cur.fetchone() is None:
            raise FuelError("Employé introuvable")

        # Insertion
        cur.execute(
            """
            INSERT INTO ravitaillements
            (vehicule_id, employe_id, date, quantite_litres, cout, kilometrage, station)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vehicule_id,
                employe_id,
                date,
                quantite_litres,
                cout,
                kilometrage,
                station,
            ),
        )
        conn.commit()


# =========================================================
# CALCUL DERNIÈRE CONSOMMATION (L / 100 KM)
# =========================================================
def compute_last_consumption_l_per_100km(
    vehicule_id: int,
    db_path="db/parc_auto.db",
):
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT quantite_litres, kilometrage
            FROM ravitaillements
            WHERE vehicule_id = ?
              AND kilometrage IS NOT NULL
            ORDER BY date DESC, id DESC
            LIMIT 2
            """,
            (vehicule_id,),
        )
        rows = cur.fetchall()

    if len(rows) < 2:
        return None

    dernier = rows[0]
    precedent = rows[1]

    km_parcourus = dernier["kilometrage"] - precedent["kilometrage"]
    if km_parcourus <= 0:
        return None

    return round((dernier["quantite_litres"] / km_parcourus) * 100, 2)


# =========================================================
# MÉTHODE APPELÉE PAR L’INTERFACE
# =========================================================
def add_fuel_entry(
    vehicule_id: int,
    employe_id: int,
    date: str,
    quantite_litres: float,
    cout: float,
    kilometrage: int | None = None,
    station: str | None = None,
):
    record_fuel(
        vehicule_id=vehicule_id,
        employe_id=employe_id,
        date=date,
        quantite_litres=quantite_litres,
        cout=cout,
        kilometrage=kilometrage,
        station=station,
    )

    # Le calcul est conservé pour usage futur (stats, alertes, etc.)
    return compute_last_consumption_l_per_100km(vehicule_id)


# =========================================================
# LECTURE DES RAVITAILLEMENTS
# AVEC CONSOMMATION MOYENNE PAR LIGNE
# =========================================================
def get_all_fuel_entries(db_path="db/parc_auto.db"):
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                r.date,
                r.quantite_litres,
                r.cout,
                r.kilometrage,
                v.immatriculation,
                e.prenom,
                e.nom,

                ROUND(
                    (r.quantite_litres * 100.0) /
                    (
                        r.kilometrage -
                        (
                            SELECT r2.kilometrage
                            FROM ravitaillements r2
                            WHERE r2.vehicule_id = r.vehicule_id
                              AND r2.kilometrage IS NOT NULL
                              AND r2.date < r.date
                            ORDER BY r2.date DESC, r2.id DESC
                            LIMIT 1
                        )
                    ),
                    2
                ) AS consommation

            FROM ravitaillements r
            JOIN vehicules v ON v.id = r.vehicule_id
            JOIN employes e ON e.id = r.employe_id
            ORDER BY r.date DESC, r.id DESC
            """
        )
        return cur.fetchall()