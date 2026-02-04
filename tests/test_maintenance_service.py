import unittest
from pathlib import Path
import uuid
import gc

from database import init_db, get_connection
from services.maintenance_service import (
    record_maintenance,
    get_maintenances_for_vehicle,
    MaintenanceError,
)


class TestMaintenanceService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"maint_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO vehicules (
                    immatriculation, marque, modele,
                    type_vehicule, type_affectation, statut
                ) VALUES (?, ?, ?, ?, ?, 'disponible')
                """,
                ("MA-001", "Renault", "Clio", "voiture", "mutualise"),
            )
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("maint_*.db"):
            try:
                f.unlink()
            except PermissionError:
                pass

    def test_record_maintenance_success(self):
        with get_connection(self.db_path) as conn:
            vehicule_id = conn.execute(
                "SELECT id FROM vehicules"
            ).fetchone()["id"]

        record_maintenance(
            vehicule_id=vehicule_id,
            date_="2026-01-01",
            type_intervention="vidange",
            kilometrage=1200,
            cout=199.99,
            prestataire="Garage X",
            db_path=self.db_path,
        )

        maints = get_maintenances_for_vehicle(vehicule_id, self.db_path)
        self.assertEqual(len(maints), 1)
        self.assertEqual(maints[0]["type_intervention"], "vidange")

    def test_vehicle_not_found(self):
        with self.assertRaises(MaintenanceError):
            record_maintenance(
                vehicule_id=9999,
                date_="2026-01-01",
                type_intervention="pneus",
                db_path=self.db_path,
            )
