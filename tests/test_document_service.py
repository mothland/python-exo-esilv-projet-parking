import unittest
from pathlib import Path
import uuid
import gc
from datetime import date, timedelta

from database import init_db, get_connection
from services.document_service import (
    add_document,
    get_documents_for_vehicle,
    get_expiring_documents,
    DocumentError,
)


class TestDocumentService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"doc_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO vehicules (
                    immatriculation, marque, modele,
                    type_vehicule, type_affectation, statut
                ) VALUES (?, ?, ?, ?, ?, 'disponible')
                """,
                ("DOC-001", "Renault", "Clio", "voiture", "mutualise"),
            )
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("doc_*.db"):
            try:
                f.unlink()
            except PermissionError:
                pass

    def _vehicule_id(self):
        with get_connection(self.db_path) as conn:
            return conn.execute(
                "SELECT id FROM vehicules"
            ).fetchone()["id"]

    def test_add_document_vehicle(self):
        vehicule_id = self._vehicule_id()

        add_document(
            vehicule_id=vehicule_id,
            type_document="Assurance",
            chemin_fichier="docs/assurance.pdf",
            date_echeance="2026-12-31",
            db_path=self.db_path,
        )

        docs = get_documents_for_vehicle(vehicule_id, self.db_path)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["type_document"], "Assurance")

    def test_expiring_documents(self):
        vehicule_id = self._vehicule_id()

        soon = (date.today() + timedelta(days=5)).isoformat()

        add_document(
            vehicule_id=vehicule_id,
            type_document="CT",
            chemin_fichier="docs/ct.pdf",
            date_echeance=soon,
            db_path=self.db_path,
        )

        expiring = get_expiring_documents(30, self.db_path)
        self.assertEqual(len(expiring), 1)

    def test_missing_vehicle_rejected(self):
        with self.assertRaises(DocumentError):
            add_document(
                vehicule_id=None,
                type_document="X",
                chemin_fichier="x.pdf",
                db_path=self.db_path,
            )
