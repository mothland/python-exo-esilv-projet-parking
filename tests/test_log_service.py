import unittest
from pathlib import Path
import uuid
import gc

from database import init_db
from services.log_service import log_action, get_logs


class TestLogService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path("tests/_tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db_path = self.tmp_dir / f"log_{uuid.uuid4().hex}.db"
        init_db(self.db_path)

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        for f in cls.tmp_dir.glob("log_*.db"):
            try:
                f.unlink()
            except PermissionError:
                pass

    def test_log_written(self):
        log_action(
            action="LOGIN",
            user_id=None,
            details="User logged in",
            db_path=self.db_path,
        )

        logs = get_logs(db_path=self.db_path)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "LOGIN")

    def test_action_required(self):
        with self.assertRaises(ValueError):
            log_action(action="", db_path=self.db_path)
