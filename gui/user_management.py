import tkinter as tk
from tkinter import ttk, messagebox

from services.user_service import create_user, UserCreationError


class UserManagementWindow(tk.Toplevel):

    def __init__(self, db_path="db/parc_auto.db"):
        super().__init__()

        self.db_path = db_path

        self.title("Gestion des utilisateurs")
        self.geometry("400x420")
        self.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        def labeled_entry(label, show=None):
            ttk.Label(frame, text=label).pack(anchor="w", pady=(10, 2))
            entry = ttk.Entry(frame, show=show)
            entry.pack(fill="x")
            return entry

        self.username_entry = labeled_entry("Nom d'utilisateur")
        self.password_entry = labeled_entry("Mot de passe", show="*")
        self.nom_entry = labeled_entry("Nom")
        self.prenom_entry = labeled_entry("Prénom")
        self.email_entry = labeled_entry("Email (optionnel)")

        ttk.Label(frame, text="Rôle").pack(anchor="w", pady=(10, 2))
        self.role_var = tk.StringVar(value="Employe")
        self.role_combo = ttk.Combobox(
            frame,
            textvariable=self.role_var,
            values=["Admin", "Gestionnaire", "Employe"],
            state="readonly",
        )
        self.role_combo.pack(fill="x")

        ttk.Button(
            frame,
            text="Créer l'utilisateur",
            command=self._create_user,
        ).pack(pady=20)

    def _create_user(self):
        try:
            create_user(
                username=self.username_entry.get().strip(),
                password=self.password_entry.get().strip(),
                role=self.role_var.get(),
                nom=self.nom_entry.get().strip(),
                prenom=self.prenom_entry.get().strip(),
                email=self.email_entry.get().strip() or None,
                db_path=self.db_path,
            )
        except UserCreationError as e:
            messagebox.showerror("Erreur", str(e))
            return

        messagebox.showinfo(
            "Succès",
            "Utilisateur créé avec succès",
        )
        self.destroy()
