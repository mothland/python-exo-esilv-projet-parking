# utils/demo_data.py
from datetime import date, datetime, timedelta
import random

from database import get_connection
from utils.hashing import hash_password


def seed_demo_data(db_path="db/parc_auto.db"):
    with get_connection(db_path) as conn:
        cur = conn.cursor()

        # prevent double seeding
        cur.execute("SELECT COUNT(*) FROM vehicules")
        if cur.fetchone()[0] > 0:
            return

        seed_users(cur)
        seed_employees(cur)
        seed_vehicles(cur)
        seed_affectations(cur)
        seed_reservations(cur)
        seed_maintenances(cur)
        seed_fuel(cur)
        seed_documents(cur)

        conn.commit()

def seed_users(cur):
    users = [
        ("admin", hash_password("admin123"), "Admin", "Root", "Admin", "admin@company.com"),
        ("gestion", hash_password("gestion123"), "Gestionnaire", "Paul", "Martin", "paul.martin@company.com"),
        ("employe", hash_password("employe123"), "Employé", "Julie", "Durand", "julie.durand@company.com"),
    ]

    for u in users:
        cur.execute("""
            INSERT INTO users (username, password_hash, role, nom, prenom, email, actif)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, u)

def seed_employees(cur):
    services = ["Commercial", "Technique", "RH", "Logistique", "Direction"]

    for i in range(1, 9):
        cur.execute("""
            INSERT INTO employes (
                matricule, nom, prenom, service, telephone, email,
                num_permis, date_validite_permis, autorise_conduire
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            f"EMP{i:03}",
            f"Nom{i}",
            f"Prenom{i}",
            random.choice(services),
            f"06000000{i}",
            f"user{i}@company.com",
            f"PERMIS{i:05}",
            date.today() + timedelta(days=random.choice([15, 45, 120, 400]))
        ))

def seed_vehicles(cur):
    vehicles = [
        # immat, marque, modele, type, carburant, statut
        ("AA-123-AA", "Peugeot", "308", "Voiture", "Essence", "disponible"),
        ("BB-456-BB", "Renault", "Kangoo", "Utilitaire", "Diesel", "en_sortie"),
        ("CC-789-CC", "Tesla", "Model 3", "Voiture", "Électrique", "en_maintenance"),
        ("DD-321-DD", "Citroën", "Berlingo", "Camionnette", "Diesel", "disponible"),
        ("EE-654-EE", "Toyota", "Corolla", "Voiture", "Hybride", "en_panne"),
    ]

    for imm, marque, modele, t, carb, statut in vehicles:
        cur.execute(
            """
            INSERT INTO vehicules (
                immatriculation,
                marque,
                modele,
                type_vehicule,
                annee,
                date_acquisition,
                kilometrage_actuel,
                carburant,
                puissance_fiscale,
                type_affectation,
                statut,
                service_principal,
                seuil_revision_km
            )
            VALUES (?, ?, ?, ?, 2020, ?, ?, ?, 6, ?, ?, ?, 15000)
            """,
            (
                imm,
                marque,
                modele,
                t,
                date.today() - timedelta(days=900),
                random.randint(20_000, 80_000),
                carb,
                random.choice(["mutualisé", "fonction"]),
                statut,
                random.choice(["Commercial", "Technique", "Logistique"]),
            ),
        )

def seed_reservations(cur):
    for _ in range(20):
        start = datetime.now() - timedelta(days=random.randint(1, 30))
        end = start + timedelta(hours=random.randint(2, 10))

        cur.execute("""
            INSERT INTO sorties_reservations (
                vehicule_id, employe_id,
                date_sortie_reelle, heure_sortie_reelle,
                date_retour_reelle, heure_retour_reelle,
                km_depart, km_retour,
                motif, destination, statut
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'terminée'
            )
        """, (
            random.randint(1, 5),
            random.randint(1, 8),
            start.date(), start.time().strftime("%H:%M"),
            end.date(), end.time().strftime("%H:%M"),
            50000,
            50000 + random.randint(10, 250),
            random.choice(["Rendez-vous client", "Livraison", "Déplacement pro"]),
            random.choice(["Paris", "Lyon", "Marseille", "Lille"])
        ))

def seed_maintenances(cur):
    for _ in range(10):
        km = random.randint(30000, 90000)
        cur.execute("""
            INSERT INTO maintenances (
                vehicule_id, date, type_intervention,
                kilometrage, cout, prestataire, remarques,
                date_prochaine_echeance
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            random.randint(1, 5),
            date.today() - timedelta(days=random.randint(30, 400)),
            random.choice(["Vidange", "Pneus", "Freins", "Révision"]),
            km,
            random.randint(120, 1200),
            "Garage Central",
            "RAS",
            date.today() + timedelta(days=random.randint(30, 180))
        ))

def seed_fuel(cur):
    for _ in range(25):
        cur.execute("""
            INSERT INTO ravitaillements (
                vehicule_id, employe_id, date,
                quantite_litres, cout, station, kilometrage
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            random.randint(1, 5),
            random.randint(1, 8),
            date.today() - timedelta(days=random.randint(1, 90)),
            round(random.uniform(20, 60), 1),
            round(random.uniform(40, 120), 2),
            random.choice(["Total", "Shell", "BP"]),
            random.randint(30000, 90000)
        ))

def seed_affectations(cur):
    """
    Create permanent assignments for 'voiture de fonction'.
    Each function vehicle is assigned to an employee.
    """

    # fetch fonction vehicles
    cur.execute("""
        SELECT id
        FROM vehicules
        WHERE type_affectation = 'fonction'
    """)
    vehicules = [row[0] for row in cur.fetchall()]

    if not vehicules:
        return

    # fetch employees
    cur.execute("SELECT id FROM employes")
    employes = [row[0] for row in cur.fetchall()]

    if not employes:
        return

    today = date.today()

    for idx, vehicule_id in enumerate(vehicules):
        employe_id = employes[idx % len(employes)]

        cur.execute("""
            INSERT INTO affectations_permanentes (
                vehicule_id,
                employe_id,
                date_debut,
                date_fin
            )
            VALUES (?, ?, ?, NULL)
        """, (
            vehicule_id,
            employe_id,
            today - timedelta(days=random.randint(30, 600))
        ))

def seed_documents(cur):
    """
    Insert administrative documents for vehicles
    (insurance, inspection, registration...)
    """

    cur.execute("SELECT id FROM vehicules")
    vehicules = [row[0] for row in cur.fetchall()]

    if not vehicules:
        return

    today = date.today()

    doc_types = [
        "Assurance",
        "Contrôle technique",
        "Carte grise",
        "Vignette"
    ]

    for vehicule_id in vehicules:
        for doc_type in random.sample(doc_types, k=2):
            cur.execute("""
                INSERT INTO documents (
                    vehicule_id,
                    type_document,
                    date_emission,
                    date_echeance,
                    chemin_fichier,
                    description
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                vehicule_id,
                doc_type,
                today - timedelta(days=random.randint(30, 300)),
                today + timedelta(days=random.randint(60, 365)),
                f"docs/{doc_type.lower().replace(' ', '_')}_{vehicule_id}.pdf",
                f"{doc_type} du véhicule"
            ))
