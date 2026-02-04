from database import get_connection


class FuelError(Exception):
    pass


def record_fuel(
    vehicule_id: int,
    employe_id: int,
    date_: str,
    quantite_litres: float,
    cout: float,
    station: str | None = None,
    kilometrage: int | None = None,
    db_path="db/parc_auto.db",
):
    if not date_:
        raise FuelError("Date requise")
    if quantite_litres is None or quantite_litres <= 0:
        raise FuelError("Quantité invalide")
    if cout is None or cout < 0:
        raise FuelError("Coût invalide")

    with get_connection(db_path) as conn:
        cur = conn.cursor()

        # Vehicle exists?
        cur.execute("SELECT id FROM vehicules WHERE id = ?", (vehicule_id,))
        if cur.fetchone() is None:
            raise FuelError("Véhicule introuvable")

        # Employee exists?
        cur.execute("SELECT id FROM employes WHERE id = ?", (employe_id,))
        if cur.fetchone() is None:
            raise FuelError("Employé introuvable")

        cur.execute(
            """
            INSERT INTO ravitaillements (
                vehicule_id, employe_id, date,
                quantite_litres, cout, station, kilometrage
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vehicule_id,
                employe_id,
                date_,
                quantite_litres,
                cout,
                station,
                kilometrage,
            ),
        )
        conn.commit()


def compute_last_consumption_l_per_100km(
    vehicule_id: int,
    db_path="db/parc_auto.db",
):
    """
    Compute L/100km based on the last two fuel events that have kilometrage.
    Returns None if not enough data.
    """
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

    latest = rows[0]
    previous = rows[1]

    km_delta = latest["kilometrage"] - previous["kilometrage"]
    if km_delta <= 0:
        return None

    return (latest["quantite_litres"] / km_delta) * 100.0


def add_fuel_entry(
    vehicule_id: int,
    employe_id: int,
    date: str,
    quantite_litres: float,
    cout: float,
    station: str | None = None,
    kilometrage: int | None = None,
    db_path="db/parc_auto.db",
):
    """
    UI-facing helper for recording a fuel entry.
    """
    return record_fuel(
        vehicule_id=vehicule_id,
        employe_id=employe_id,
        date_=date,
        quantite_litres=quantite_litres,
        cout=cout,
        station=station,
        kilometrage=kilometrage,
        db_path=db_path,
    )


def get_all_fuel_entries(db_path="db/parc_auto.db"):
    """
    Return all fuel entries with vehicle and employee info.
    """
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
                e.nom
            FROM ravitaillements r
            JOIN vehicules v ON v.id = r.vehicule_id
            JOIN employes e ON e.id = r.employe_id
            ORDER BY r.date DESC
            """
        )
        return cur.fetchall()
