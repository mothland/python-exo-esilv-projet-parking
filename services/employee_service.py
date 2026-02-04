from datetime import date
from database import get_connection


class EmployeeError(Exception):
    pass


def is_permis_valid(date_validite_permis: str) -> bool:
    """
    Check if a driving license is still valid.
    Expected format: YYYY-MM-DD
    """
    if not date_validite_permis:
        return False

    return date.fromisoformat(date_validite_permis) >= date.today()


def create_employee(
    matricule: str,
    nom: str,
    prenom: str,
    service: str | None = None,
    telephone: str | None = None,
    email: str | None = None,
    num_permis: str | None = None,
    date_validite_permis: str | None = None,
    autorise_conduire: int = 0,
    photo_path: str | None = None,
    db_path="db/parc_auto.db",
):
    if not matricule or not nom or not prenom:
        raise EmployeeError("Matricule, nom et prénom sont obligatoires")

    if autorise_conduire:
        if not num_permis or not date_validite_permis:
            raise EmployeeError(
                "Permis requis pour autoriser la conduite"
            )
        if not is_permis_valid(date_validite_permis):
            raise EmployeeError(
                "Permis de conduire expiré"
            )

    try:
        with get_connection(db_path) as conn:
            conn.execute(
                """
                INSERT INTO employes (
                    matricule, nom, prenom, service,
                    telephone, email,
                    num_permis, date_validite_permis,
                    autorise_conduire, photo_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    matricule,
                    nom,
                    prenom,
                    service,
                    telephone,
                    email,
                    num_permis,
                    date_validite_permis,
                    autorise_conduire,
                    photo_path,
                ),
            )
            conn.commit()
    except Exception as e:
        raise EmployeeError(str(e))


def get_authorized_employees(db_path="db/parc_auto.db"):
    """
    Return employees authorized to drive.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM employes
            WHERE autorise_conduire = 1
            ORDER BY nom, prenom
            """
        )
        return cur.fetchall()

def get_all_employees(db_path="db/parc_auto.db"):
    """
    Return all employees.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM employes
            ORDER BY nom, prenom
            """
        )
        return cur.fetchall()
