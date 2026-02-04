import unittest
from utils.hashing import hash_password, verify_password


class TestHashing(unittest.TestCase):

    def test_hash_format(self):
        hashed = hash_password("secret")
        parts = hashed.split("$")
        self.assertEqual(len(parts), 3)
        self.assertTrue(parts[0].isdigit())

    def test_same_password_different_hashes(self):
        h1 = hash_password("secret")
        h2 = hash_password("secret")
        self.assertNotEqual(h1, h2)

    def test_verify_correct_password(self):
        hashed = hash_password("secret")
        self.assertTrue(verify_password("secret", hashed))

    def test_verify_wrong_password(self):
        hashed = hash_password("secret")
        self.assertFalse(verify_password("wrong", hashed))

    def test_empty_password_rejected(self):
        with self.assertRaises(ValueError):
            hash_password("")


if __name__ == "__main__":
    unittest.main()
