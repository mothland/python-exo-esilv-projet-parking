import os
import hashlib
import hmac

_ITERATIONS = 120_000
_SALT_SIZE = 16
_HASH_NAME = "sha256"


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC.
    Returns a string: iterations$salt_hex$hash_hex
    """
    if not password:
        raise ValueError("Password cannot be empty")

    salt = os.urandom(_SALT_SIZE)
    dk = hashlib.pbkdf2_hmac(
        _HASH_NAME,
        password.encode("utf-8"),
        salt,
        _ITERATIONS
    )

    return f"{_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored hash.
    """
    try:
        iterations_str, salt_hex, hash_hex = stored_hash.split("$")
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
    except Exception:
        return False

    dk = hashlib.pbkdf2_hmac(
        _HASH_NAME,
        password.encode("utf-8"),
        salt,
        iterations
    )

    return hmac.compare_digest(dk, expected_hash)
