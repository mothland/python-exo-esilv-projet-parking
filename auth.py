from typing import Optional, Dict
from database import get_connection
from utils.hashing import verify_password


class AuthError(Exception):
    pass


def authenticate_user(
    username: str,
    password: str,
    db_path="db/parc_auto.db"
) -> Dict:
    """
    Authenticate a user.
    Returns a dict with user info if successful.
    Raises AuthError otherwise.
    """
    if not username or not password:
        raise AuthError("Username and password required")

    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, username, password_hash, role, nom, prenom, email, actif
            FROM users
            WHERE username = ?
            """,
            (username,)
        )
        row = cur.fetchone()

    if row is None:
        raise AuthError("Invalid credentials")

    if not row["actif"]:
        raise AuthError("User account is inactive")

    if not verify_password(password, row["password_hash"]):
        raise AuthError("Invalid credentials")

    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "nom": row["nom"],
        "prenom": row["prenom"],
        "email": row["email"],
    }
