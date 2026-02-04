import unittest
from pathlib import Path
import uuid
import gc

from database import init_db, get_connection
from services.fuel_service import (
    record_fuel,
    compute_last_consumption_l_per_100km,
    FuelError,
)


class TestFuelService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"fuel_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO vehicules (
                    immatriculation, marque, modele,
                    type_vehicule, type_affectation, statut
                ) VALUES (?, ?, ?, ?, ?, 'disponible')
                """,
                ("FU-001", "Peugeot", "208", "voiture", "mutualise"),
            )
            conn.execute(
                """
                INSERT INTO employes (
                    matricule, nom, prenom, autorise_conduire
                ) VALUES (?, ?, ?, 1)
                """,
                ("EMPX", "Doe", "Jane"),
            )
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("fuel_*.db"):
            try:
                f.unlink()
            except PermissionError:
                pass

    def _ids(self):
        with get_connection(self.db_path) as conn:
            vehicule_id = conn.execute(
                "SELECT id FROM vehicules"
            ).fetchone()["id"]
            employe_id = conn.execute(
                "SELECT id FROM employes"
            ).fetchone()["id"]
        return vehicule_id, employe_id

    def test_record_fuel_success(self):
        vehicule_id, employe_id = self._ids()

        record_fuel(
            vehicule_id=vehicule_id,
            employe_id=employe_id,
            date_="2026-01-01",
            quantite_litres=40.0,
            cout=80.0,
            station="Total",
            kilometrage=1000,
            db_path=self.db_path,
        )

    def test_consumption_requires_two_events(self):
        vehicule_id, employe_id = self._ids()

        record_fuel(
            vehicule_id=vehicule_id,
            employe_id=employe_id,
            date_="2026-01-01",
            quantite_litres=40.0,
            cout=80.0,
            kilometrage=1000,
            db_path=self.db_path,
        )

        self.assertIsNone(
            compute_last_consumption_l_per_100km(vehicule_id, self.db_path)
        )

        record_fuel(
            vehicule_id=vehicule_id,
            employe_id=employe_id,
            date_="2026-01-10",
            quantite_litres=30.0,
            cout=60.0,
            kilometrage=1500,
            db_path=self.db_path,
        )

        cons = compute_last_consumption_l_per_100km(vehicule_id, self.db_path)
        self.assertIsNotNone(cons)

        # 30L over 500km -> 6.0 L/100km
        self.assertAlmostEqual(cons, 6.0, places=2)

    def test_invalid_quantity(self):
        vehicule_id, employe_id = self._ids()
        with self.assertRaises(FuelError):
            record_fuel(
                vehicule_id=vehicule_id,
                employe_id=employe_id,
                date_="2026-01-01",
                quantite_litres=0,
                cout=10,
                db_path=self.db_path,
            )
