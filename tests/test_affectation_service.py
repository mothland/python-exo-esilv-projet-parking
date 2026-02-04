import unittest
from pathlib import Path
import uuid
import gc

from database import init_db, get_connection
from services.affectation_service import (
    create_affectation,
    get_active_affectation,
    end_affectation,
    AffectationError,
)


class TestAffectationService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"aff_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO vehicules (
                    immatriculation, marque, modele,
                    type_vehicule, type_affectation, statut
                ) VALUES (?, ?, ?, ?, ?, 'disponible')
                """,
                ("FUNC-001", "Renault", "Megane", "voiture", "fonction"),
            )

            conn.execute(
                """
                INSERT INTO employes (
                    matricule, nom, prenom, autorise_conduire
                ) VALUES (?, ?, ?, 1)
                """,
                ("EMP-FUNC", "Doe", "Jane"),
            )
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("aff_*.db"):
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

    def test_create_and_get_affectation(self):
        vehicule_id, employe_id = self._ids()

        create_affectation(
            vehicule_id=vehicule_id,
            employe_id=employe_id,
            date_debut="2026-01-01",
            db_path=self.db_path,
        )

        aff = get_active_affectation(vehicule_id, self.db_path)
        self.assertIsNotNone(aff)
        self.assertEqual(aff["employe_id"], employe_id)

    def test_end_affectation(self):
        vehicule_id, employe_id = self._ids()

        create_affectation(
            vehicule_id=vehicule_id,
            employe_id=employe_id,
            date_debut="2026-01-01",
            db_path=self.db_path,
        )

        with get_connection(self.db_path) as conn:
            aff_id = conn.execute(
                "SELECT id FROM affectations_permanentes"
            ).fetchone()["id"]

        end_affectation(
            affectation_id=aff_id,
            date_fin="2026-12-31",
            db_path=self.db_path,
        )

        aff = get_active_affectation(vehicule_id, self.db_path)
        self.assertIsNone(aff)
