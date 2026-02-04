import unittest
from pathlib import Path
import uuid
import gc

from database import init_db
from services.user_service import create_user, UserCreationError


class TestUserService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"user_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("user_*.db"):
            try:
                f.unlink()
            except PermissionError:
                pass

    def test_create_user_success(self):
        create_user(
            username="admin",
            password="secret",
            role="Admin",
            nom="Root",
            prenom="User",
            db_path=self.db_path,
        )

    def test_duplicate_username(self):
        create_user(
            username="admin",
            password="secret",
            role="Admin",
            nom="Root",
            prenom="User",
            db_path=self.db_path,
        )

        with self.assertRaises(UserCreationError):
            create_user(
                username="admin",
                password="other",
                role="Admin",
                nom="Dup",
                prenom="User",
                db_path=self.db_path,
            )

    def test_invalid_role(self):
        with self.assertRaises(UserCreationError):
            create_user(
                username="x",
                password="y",
                role="Hacker",
                nom="Bad",
                prenom="Guy",
                db_path=self.db_path,
            )
