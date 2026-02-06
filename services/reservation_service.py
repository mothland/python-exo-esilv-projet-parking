from datetime import datetime
from database import get_connection


class ReservationError(Exception):
    pass


# =========================================================
# LECTURE DES RÉSERVATIONS
# =========================================================

def get_all_reservations():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            sr.id,
            v.immatriculation,
            e.prenom,
            e.nom,
            sr.date_sortie_prevue,
            sr.heure_sortie_prevue,
            sr.date_retour_prevue,
            sr.heure_retour_prevue,
            sr.date_sortie_reelle,
            sr.date_retour_reelle,
            sr.statut
        FROM sorties_reservations sr
        JOIN vehicules v ON v.id = sr.vehicule_id
        JOIN employes e ON e.id = sr.employe_id
        ORDER BY sr.id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [{
        "id": r[0],
        "immatriculation": r[1],
        "prenom": r[2],
        "nom": r[3],
        "date_sortie_prevue": r[4],
        "heure_sortie_prevue": r[5],
        "date_retour_prevue": r[6],
        "heure_retour_prevue": r[7],
        "date_sortie_reelle": r[8],
        "date_retour_reelle": r[9],
        "statut": r[10],
    } for r in rows]


# =========================================================
# CRÉATION D’UNE RÉSERVATION / SORTIE
# =========================================================

def create_reservation(
    vehicule_id,
    employe_id,
    date_sortie_prevue,
    heure_sortie_prevue,
    date_retour_prevue,
    heure_retour_prevue,
    km_depart,
    motif,
    destination
):
    conn = get_connection()
    cur = conn.cursor()

    # 🔒 Vérifier véhicule
    cur.execute(
        "SELECT statut, kilometrage_actuel FROM vehicules WHERE id = ?",
        (vehicule_id,)
    )
    veh = cur.fetchone()

    if not veh:
        conn.close()
        raise ReservationError("Véhicule introuvable")

    statut_vehicule, km_actuel = veh
    km_actuel = km_actuel or 0

    if statut_vehicule != "disponible":
        conn.close()
        raise ReservationError("Véhicule non disponible")

    if km_depart < km_actuel:
        conn.close()
        raise ReservationError(
            f"Kilométrage départ invalide (kilométrage actuel : {km_actuel})"
        )

    # 🔒 Vérifier employé
    cur.execute(
        "SELECT autorise_conduire FROM employes WHERE id = ?",
        (employe_id,)
    )
    emp = cur.fetchone()

    if not emp or emp[0] != 1:
        conn.close()
        raise ReservationError("Employé non autorisé à conduire")

    # 🔒 Vérifier dates
    if date_retour_prevue and date_retour_prevue < date_sortie_prevue:
        conn.close()
        raise ReservationError("Date de retour antérieure à la date de sortie")

    # ➕ Insertion sortie
    cur.execute("""
        INSERT INTO sorties_reservations (
            vehicule_id,
            employe_id,
            date_sortie_prevue,
            heure_sortie_prevue,
            date_retour_prevue,
            heure_retour_prevue,
            km_depart,
            motif,
            destination,
            statut
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'en sortie')
    """, (
        vehicule_id,
        employe_id,
        date_sortie_prevue,
        heure_sortie_prevue,
        date_retour_prevue,
        heure_retour_prevue,
        km_depart,
        motif,
        destination
    ))

    # 🚗 Mise à jour véhicule
    cur.execute("""
        UPDATE vehicules
        SET
            kilometrage_actuel = ?,
            statut = 'en sortie'
        WHERE id = ?
    """, (km_depart, vehicule_id))

    conn.commit()
    conn.close()


# =========================================================
# RETOUR DE VÉHICULE
# =========================================================

def return_vehicle(reservation_id, km_retour, etat_retour, niveau_carburant):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT vehicule_id, km_depart
        FROM sorties_reservations
        WHERE id = ? AND statut = 'en sortie'
    """, (reservation_id,))

    row = cur.fetchone()
    if not row:
        conn.close()
        raise ReservationError("Sortie invalide ou déjà clôturée")

    vehicule_id, km_depart = row

    if km_retour < km_depart:
        conn.close()
        raise ReservationError("Kilométrage retour inférieur au départ")

    now = datetime.now()

    # 🔄 Mise à jour sortie
    cur.execute("""
        UPDATE sorties_reservations
        SET
            date_retour_reelle = ?,
            heure_retour_reelle = ?,
            km_retour = ?,
            etat_retour = ?,
            niveau_carburant_retour = ?,
            statut = 'terminée'
        WHERE id = ?
    """, (
        now.date().isoformat(),
        now.strftime("%H:%M"),
        km_retour,
        etat_retour,
        niveau_carburant,
        reservation_id
    ))

    # 🚘 Nouveau statut véhicule
    if etat_retour == "propre":
        statut = "disponible"
    elif etat_retour == "sale":
        statut = "a nettoyer"
    else:
        statut = "en maintenance"

    cur.execute("""
        UPDATE vehicules
        SET
            kilometrage_actuel = ?,
            statut = ?
        WHERE id = ?
    """, (km_retour, statut, vehicule_id))

    conn.commit()
    conn.close()