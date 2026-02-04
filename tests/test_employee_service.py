import unittest
from pathlib import Path
import uuid
import gc
from datetime import date, timedelta

from database import init_db
from services.employee_service import (
    create_employee,
    get_authorized_employees,
    EmployeeError,
)


class TestEmployeeService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"employee_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("employee_*.db"):
            try:
                f.unlink()
            except PermissionError:
                pass

    def test_create_employee_minimal(self):
        create_employee(
            matricule="EMP001",
            nom="Doe",
            prenom="John",
            db_path=self.db_path,
        )

    def test_authorized_employee_valid_permis(self):
        valid_date = (date.today() + timedelta(days=30)).isoformat()

        create_employee(
            matricule="EMP002",
            nom="Driver",
            prenom="Jane",
            num_permis="PERMIS123",
            date_validite_permis=valid_date,
            autorise_conduire=1,
            db_path=self.db_path,
        )

        employees = get_authorized_employees(self.db_path)
        self.assertEqual(len(employees), 1)
        self.assertEqual(employees[0]["matricule"], "EMP002")

    def test_expired_permis_rejected(self):
        expired_date = (date.today() - timedelta(days=1)).isoformat()

        with self.assertRaises(EmployeeError):
            create_employee(
                matricule="EMP003",
                nom="Old",
                prenom="Driver",
                num_permis="OLD123",
                date_validite_permis=expired_date,
                autorise_conduire=1,
                db_path=self.db_path,
            )

    def test_duplicate_matricule(self):
        create_employee(
            matricule="EMP004",
            nom="Dup",
            prenom="User",
            db_path=self.db_path,
        )

        with self.assertRaises(EmployeeError):
            create_employee(
                matricule="EMP004",
                nom="Dup2",
                prenom="User2",
                db_path=self.db_path,
            )
