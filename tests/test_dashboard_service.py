import unittest
from pathlib import Path
import uuid
import gc

from database import init_db, get_connection
from services.dashboard_service import (
    get_fleet_summary,
    get_available_vehicles,
)


class TestDashboardService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"dashboard_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO vehicules (
                    immatriculation, marque, modele,
                    type_vehicule, type_affectation, statut
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    ("AA-001", "Renault", "Clio", "voiture", "mutualise", "disponible"),
                    ("BB-002", "Peugeot", "208", "voiture", "mutualise", "en_sortie"),
                    ("CC-003", "Citroen", "C3", "voiture", "mutualise", "en_maintenance"),
                ],
            )
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("dashboard_*.db"):
            try:
                f.unlink()
            except PermissionError:
                pass

    def test_fleet_summary_counts(self):
        summary = get_fleet_summary(self.db_path)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["available"], 1)
        self.assertEqual(summary["en_sortie"], 1)
        self.assertEqual(summary["maintenance"], 1)
        self.assertFalse(summary["parc_complet"])

    def test_parc_complet(self):
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE vehicules SET statut = 'en_sortie'"
            )
            conn.commit()

        summary = get_fleet_summary(self.db_path)
        self.assertTrue(summary["parc_complet"])

    def test_available_vehicles(self):
        vehicles = get_available_vehicles(self.db_path)

        self.assertEqual(len(vehicles), 1)
        self.assertEqual(vehicles[0]["immatriculation"], "AA-001")
