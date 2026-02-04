import unittest
from pathlib import Path
import uuid
import gc
from datetime import date, timedelta

from database import init_db, get_connection
from services.alert_service import (
    get_document_alerts,
    get_maintenance_alerts,
    get_revision_km_alerts,
)


class TestAlertService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"alert_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO vehicules (
                    immatriculation, marque, modele,
                    type_vehicule, type_affectation,
                    statut, kilometrage_actuel, seuil_revision_km
                ) VALUES (?, ?, ?, ?, ?, 'disponible', ?, ?)
                """,
                ("AL-001", "Renault", "Clio", "voiture", "mutualise", 12000, 10000),
            )

            vehicule_id = conn.execute(
                "SELECT id FROM vehicules"
            ).fetchone()["id"]

            conn.execute(
                """
                INSERT INTO documents (
                    vehicule_id, type_document,
                    date_echeance, chemin_fichier
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    vehicule_id,
                    "Assurance",
                    (date.today() + timedelta(days=5)).isoformat(),
                    "docs/assurance.pdf",
                ),
            )

            conn.execute(
                """
                INSERT INTO maintenances (
                    vehicule_id, date, type_intervention,
                    date_prochaine_echeance
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    vehicule_id,
                    "2026-01-01",
                    "Vidange",
                    date.today().isoformat(),
                ),
            )

            conn.commit()

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("alert_*.db"):
            try:
                f.unlink()
            except PermissionError:
                pass

    def test_document_alerts(self):
        alerts = get_document_alerts(30, self.db_path)
        self.assertEqual(len(alerts), 1)

    def test_maintenance_alerts(self):
        alerts = get_maintenance_alerts(self.db_path)
        self.assertEqual(len(alerts), 1)
