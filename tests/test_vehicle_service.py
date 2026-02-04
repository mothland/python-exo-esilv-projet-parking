import unittest
from pathlib import Path
import uuid
import gc

from database import init_db, get_connection
from services.vehicle_service import (
    create_vehicle,
    update_vehicle_status,
    get_vehicles,
    VehicleError,
)


class TestVehicleService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"vehicle_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("vehicle_*.db"):
            try:
                f.unlink()
            except PermissionError:
                pass

    def test_create_vehicle_success(self):
        create_vehicle(
            immatriculation="AA-123",
            marque="Renault",
            modele="Clio",
            type_vehicule="voiture",
            type_affectation="mutualise",
            db_path=self.db_path,
        )

    def test_duplicate_immatriculation(self):
        create_vehicle(
            immatriculation="BB-456",
            marque="Peugeot",
            modele="208",
            type_vehicule="voiture",
            type_affectation="mutualise",
            db_path=self.db_path,
        )

        with self.assertRaises(VehicleError):
            create_vehicle(
                immatriculation="BB-456",
                marque="Peugeot",
                modele="308",
                type_vehicule="voiture",
                type_affectation="mutualise",
                db_path=self.db_path,
            )

    def test_update_vehicle_status(self):
        create_vehicle(
            immatriculation="CC-789",
            marque="Citroen",
            modele="C3",
            type_vehicule="voiture",
            type_affectation="mutualise",
            db_path=self.db_path,
        )

        with get_connection(self.db_path) as conn:
            vid = conn.execute(
                "SELECT id FROM vehicules WHERE immatriculation = 'CC-789'"
            ).fetchone()["id"]

        update_vehicle_status(
            vehicule_id=vid,
            new_statut="en_sortie",
            db_path=self.db_path,
        )

        vehicles = get_vehicles(statut="en_sortie", db_path=self.db_path)
        self.assertEqual(len(vehicles), 1)

    def test_invalid_status_rejected(self):
        with self.assertRaises(VehicleError):
            update_vehicle_status(
                vehicule_id=999,
                new_statut="flying",
                db_path=self.db_path,
            )

    def test_filter_by_affectation(self):
        create_vehicle(
            immatriculation="DD-001",
            marque="Ford",
            modele="Focus",
            type_vehicule="voiture",
            type_affectation="fonction",
            db_path=self.db_path,
        )

        create_vehicle(
            immatriculation="DD-002",
            marque="Ford",
            modele="Fiesta",
            type_vehicule="voiture",
            type_affectation="mutualise",
            db_path=self.db_path,
        )

        fonction = get_vehicles(
            type_affectation="fonction",
            db_path=self.db_path,
        )
        self.assertEqual(len(fonction), 1)
