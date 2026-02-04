import sqlite3
from pathlib import Path
from typing import Union

DEFAULT_DB_PATH = Path("db/parc_auto.db")


def get_connection(db_path: Union[str, Path] = DEFAULT_DB_PATH):
    """
    Return a SQLite connection with foreign keys enabled.
    Caller must close the connection (use with-statement).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Union[str, Path] = DEFAULT_DB_PATH):
    """
    Initialize database schema exactly as specified in the assignment PDF.
    Safe to call multiple times.
    """
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    with get_connection(db_path) as conn:
        cur = conn.cursor()

        # ==================== USERS ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT,
            actif INTEGER DEFAULT 1
        );
        """)

        # ==================== EMPLOYES ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS employes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT UNIQUE NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            service TEXT,
            telephone TEXT,
            email TEXT,
            num_permis TEXT,
            date_validite_permis TEXT,
            autorise_conduire INTEGER DEFAULT 0,
            photo_path TEXT
        );
        """)

        # ==================== VEHICULES ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS vehicules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            immatriculation TEXT UNIQUE NOT NULL,
            marque TEXT NOT NULL,
            modele TEXT NOT NULL,
            type_vehicule TEXT NOT NULL,
            annee INTEGER,
            date_acquisition TEXT,
            kilometrage_actuel INTEGER,
            carburant TEXT,
            puissance_fiscale INTEGER,
            photo_path TEXT,
            type_affectation TEXT NOT NULL,
            statut TEXT NOT NULL,
            service_principal TEXT,
            seuil_revision_km INTEGER
        );
        """)

        # ==================== AFFECTATIONS PERMANENTES ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS affectations_permanentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicule_id INTEGER NOT NULL,
            employe_id INTEGER NOT NULL,
            date_debut TEXT NOT NULL,
            date_fin TEXT,
            FOREIGN KEY (vehicule_id) REFERENCES vehicules(id),
            FOREIGN KEY (employe_id) REFERENCES employes(id)
        );
        """)

        # ==================== SORTIES / RESERVATIONS ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sorties_reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicule_id INTEGER NOT NULL,
            employe_id INTEGER NOT NULL,
            date_sortie_prevue TEXT,
            heure_sortie_prevue TEXT,
            date_retour_prevue TEXT,
            heure_retour_prevue TEXT,
            date_sortie_reelle TEXT,
            heure_sortie_reelle TEXT,
            km_depart INTEGER,
            date_retour_reelle TEXT,
            heure_retour_reelle TEXT,
            km_retour INTEGER,
            motif TEXT,
            destination TEXT,
            etat_retour TEXT,
            niveau_carburant_retour TEXT,
            statut TEXT NOT NULL,
            FOREIGN KEY (vehicule_id) REFERENCES vehicules(id),
            FOREIGN KEY (employe_id) REFERENCES employes(id)
        );
        """)

        # ==================== MAINTENANCES ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS maintenances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicule_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            type_intervention TEXT NOT NULL,
            kilometrage INTEGER,
            cout REAL,
            prestataire TEXT,
            remarques TEXT,
            date_prochaine_echeance TEXT,
            FOREIGN KEY (vehicule_id) REFERENCES vehicules(id)
        );
        """)

        # ==================== RAVITAILLEMENTS ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ravitaillements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicule_id INTEGER NOT NULL,
            employe_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            quantite_litres REAL,
            cout REAL,
            station TEXT,
            kilometrage INTEGER,
            FOREIGN KEY (vehicule_id) REFERENCES vehicules(id),
            FOREIGN KEY (employe_id) REFERENCES employes(id)
        );
        """)

        # ==================== DOCUMENTS ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicule_id INTEGER NOT NULL,
            type_document TEXT NOT NULL,
            date_emission TEXT,
            date_echeance TEXT,
            chemin_fichier TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (vehicule_id) REFERENCES vehicules(id)
        );
        """)

        # ==================== LOGS ====================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            date_action TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)

        conn.commit()
