import unittest
from pathlib import Path
import uuid
import gc
from datetime import date, timedelta

from database import init_db, get_connection
from services.reservation_service import (
    create_sortie,
    return_vehicle,
    ReservationError,
)


class TestReservationService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"reservation_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            # Vehicle
            conn.execute(
                """
                INSERT INTO vehicules (
                    immatriculation, marque, modele,
                    type_vehicule, type_affectation, statut,
                    kilometrage_actuel
                ) VALUES (?, ?, ?, ?, ?, 'disponible', 1000)
                """,
                ("AA-111", "Renault", "Clio", "voiture", "mutualise"),
            )

            # Employee authorized
            conn.execute(
                """
                INSERT INTO employes (
                    matricule, nom, prenom,
                    autorise_conduire
                ) VALUES (?, ?, ?, 1)
                """,
                ("EMP1", "Doe", "John"),
            )

            # Employee NOT authorized
            conn.execute(
                """
                INSERT INTO employes (
                    matricule, nom, prenom,
                    autorise_conduire
                ) VALUES (?, ?, ?, 0)
                """,
                ("EMP2", "No", "Drive"),
            )

            conn.commit()

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("reservation_*.db"):
            try:
                f.unlink()
            except PermissionError:
                pass

    def _get_ids(self):
        with get_connection(self.db_path) as conn:
            v_id = conn.execute(
                "SELECT id FROM vehicules"
            ).fetchone()["id"]

            e_auth = conn.execute(
                "SELECT id FROM employes WHERE autorise_conduire = 1"
            ).fetchone()["id"]

            e_no = conn.execute(
                "SELECT id FROM employes WHERE autorise_conduire = 0"
            ).fetchone()["id"]

        return v_id, e_auth, e_no

    def test_create_sortie_success(self):
        v_id, e_auth, _ = self._get_ids()

        create_sortie(
            vehicule_id=v_id,
            employe_id=e_auth,
            km_depart=1000,
            motif="Client",
            destination="Paris",
            db_path=self.db_path,
        )

        with get_connection(self.db_path) as conn:
            statut = conn.execute(
                "SELECT statut FROM vehicules"
            ).fetchone()["statut"]

        self.assertEqual(statut, "en_sortie")

    def test_vehicle_not_available(self):
        v_id, e_auth, _ = self._get_ids()

        # First sortie
        create_sortie(
            vehicule_id=v_id,
            employe_id=e_auth,
            km_depart=1000,
            motif="A",
            destination="B",
            db_path=self.db_path,
        )

        # Second sortie should fail
        with self.assertRaises(ReservationError):
            create_sortie(
                vehicule_id=v_id,
                employe_id=e_auth,
                km_depart=1000,
                motif="A",
                destination="B",
                db_path=self.db_path,
            )

    def test_unauthorized_employee(self):
        v_id, _, e_no = self._get_ids()

        with self.assertRaises(ReservationError):
            create_sortie(
                vehicule_id=v_id,
                employe_id=e_no,
                km_depart=1000,
                motif="A",
                destination="B",
                db_path=self.db_path,
            )

    def test_return_vehicle_success(self):
        v_id, e_auth, _ = self._get_ids()

        create_sortie(
            vehicule_id=v_id,
            employe_id=e_auth,
            km_depart=1000,
            motif="Client",
            destination="Paris",
            db_path=self.db_path,
        )

        with get_connection(self.db_path) as conn:
            sortie_id = conn.execute(
                "SELECT id FROM sorties_reservations"
            ).fetchone()["id"]

        return_vehicle(
            sortie_id=sortie_id,
            km_retour=1100,
            db_path=self.db_path,
        )

        with get_connection(self.db_path) as conn:
            v = conn.execute(
                "SELECT statut, kilometrage_actuel FROM vehicules"
            ).fetchone()

        self.assertEqual(v["statut"], "disponible")
        self.assertEqual(v["kilometrage_actuel"], 1100)

    def test_invalid_km_return(self):
        v_id, e_auth, _ = self._get_ids()

        create_sortie(
            vehicule_id=v_id,
            employe_id=e_auth,
            km_depart=1000,
            motif="Client",
            destination="Paris",
            db_path=self.db_path,
        )

        with get_connection(self.db_path) as conn:
            sortie_id = conn.execute(
                "SELECT id FROM sorties_reservations"
            ).fetchone()["id"]

        with self.assertRaises(ReservationError):
            return_vehicle(
                sortie_id=sortie_id,
                km_retour=900,
                db_path=self.db_path,
            )
