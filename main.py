import tkinter as tk
from tkinter import messagebox

from auth import authenticate_user, AuthError
from database import init_db, get_connection
from gui.dashboard import DashboardWindow
from gui.user_management import UserManagementWindow


DB_PATH = "db/parc_auto.db"


def has_any_user(db_path=DB_PATH) -> bool:
    """
    Return True if at least one user exists in the database.
    Used to decide whether to show the bootstrap user creation button.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0] > 0


def route_by_role(user: dict):
    """
    Route user to the appropriate dashboard based on role.
    All roles currently land on the same dashboard.
    """
    DashboardWindow(user, db_path=DB_PATH)


class LoginWindow(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Gestion du Parc Automobile - Connexion")
        self.geometry("350x240")
        self.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="Nom d'utilisateur").pack(pady=(20, 5))
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()

        tk.Label(self, text="Mot de passe").pack(pady=(10, 5))
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        tk.Button(
            self,
            text="Se connecter",
            command=self._login
        ).pack(pady=(15, 10))

        # Bootstrap: only shown if no user exists yet
        if not has_any_user(DB_PATH):
            tk.Label(
                self,
                text="Aucun utilisateur détecté.",
                fg="gray"
            ).pack(pady=(5, 0))

            tk.Button(
                self,
                text="Créer un utilisateur (Admin)",
                command=self._open_user_creation
            ).pack(pady=5)

    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        try:
            user = authenticate_user(username, password, db_path=DB_PATH)
        except AuthError as e:
            messagebox.showerror("Erreur de connexion", str(e))
            return

        # Login successful
        self.withdraw()
        route_by_role(user)

    def _open_user_creation(self):
        """
        Open the user creation window (bootstrap mode).
        Intended for first admin creation only.
        """
        UserManagementWindow(db_path=DB_PATH)


def main():
    # Ensure database and tables exist before launching the UI
    init_db(DB_PATH)

    app = LoginWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
