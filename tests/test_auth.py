import unittest
from pathlib import Path
import uuid
import gc

from database import init_db, get_connection
from utils.hashing import hash_password
from auth import authenticate_user, AuthError


class TestAuth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        # Unique DB file per test (Windows-safe)
        self.db_path = self.tmp_dir / f"test_auth_{uuid.uuid4().hex}.db"

        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO users (
                    username, password_hash, role,
                    nom, prenom, email, actif
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "jdoe",
                    hash_password("secret"),
                    "Admin",
                    "Doe",
                    "John",
                    "jdoe@test.com",
                    1,
                )
            )

            conn.execute(
                """
                INSERT INTO users (
                    username, password_hash, role,
                    nom, prenom, email, actif
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "inactive",
                    hash_password("secret"),
                    "Employe",
                    "Sleepy",
                    "User",
                    "inactive@test.com",
                    0,
                )
            )
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        # Force GC to release SQLite handles (Windows)
        gc.collect()

        # Delete all test DB files created by this test module
        for db_file in cls.tmp_dir.glob("test_auth_*.db"):
            try:
                db_file.unlink()
            except PermissionError:
                # Extremely rare, but safe fallback
                pass

    def test_successful_login(self):
        user = authenticate_user("jdoe", "secret", self.db_path)
        self.assertEqual(user["username"], "jdoe")
        self.assertEqual(user["role"], "Admin")

    def test_wrong_password(self):
        with self.assertRaises(AuthError):
            authenticate_user("jdoe", "wrong", self.db_path)

    def test_unknown_user(self):
        with self.assertRaises(AuthError):
            authenticate_user("ghost", "secret", self.db_path)

    def test_inactive_user(self):
        with self.assertRaises(AuthError):
            authenticate_user("inactive", "secret", self.db_path)

    def test_missing_credentials(self):
        with self.assertRaises(AuthError):
            authenticate_user("", "", self.db_path)
