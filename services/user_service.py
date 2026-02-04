from database import get_connection
from utils.hashing import hash_password


class UserCreationError(Exception):
    pass


VALID_ROLES = {"Admin", "Gestionnaire", "Employe"}


def create_user(
    username: str,
    password: str,
    role: str,
    nom: str,
    prenom: str,
    email: str | None = None,
    actif: int = 1,
    db_path="db/parc_auto.db",
):
    if not username or not password:
        raise UserCreationError("Username and password required")

    if role not in VALID_ROLES:
        raise UserCreationError("Invalid role")

    password_hash = hash_password(password)

    try:
        with get_connection(db_path) as conn:
            conn.execute(
                """
                INSERT INTO users (
                    username, password_hash, role,
                    nom, prenom, email, actif
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    role,
                    nom,
                    prenom,
                    email,
                    actif,
                ),
            )
            conn.commit()
    except Exception as e:
        raise UserCreationError(str(e))
