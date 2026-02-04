import tkinter as tk
from tkinter import ttk, messagebox

from services.employee_service import (
    get_all_employees,
    create_employee,
    EmployeeError,
)



class EmployeeManagementWindow(tk.Toplevel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Gestion des employés")
        self.geometry("900x500")

        self._build_ui()
        self._load_employees()

    # ---------------- UI ----------------

    def _build_ui(self):
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(
            top_frame,
            text="➕ Ajouter un employé",
            command=self._open_add_employee
        ).pack(side=tk.LEFT)

        tk.Button(
            top_frame,
            text="🔄 Rafraîchir",
            command=self._load_employees
        ).pack(side=tk.LEFT, padx=5)

        columns = (
            "matricule",
            "nom",
            "prenom",
            "service",
            "autorise_conduire",
            "date_validite_permis",
        )

        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
        )

        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=140)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ---------------- Data ----------------

    def _load_employees(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        employees = get_all_employees()

        for e in employees:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    e["matricule"],
                    e["nom"],
                    e["prenom"],
                    e["service"],
                    "Oui" if e["autorise_conduire"] else "Non",
                    e["date_validite_permis"],
                ),
            )

    # ---------------- Actions ----------------

    def _open_add_employee(self):
        AddEmployeeWindow(self, on_save=self._load_employees)


# =========================================================
# Add Employee Popup
# =========================================================

class AddEmployeeWindow(tk.Toplevel):

    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Ajouter un employé")
        self.geometry("400x500")
        self.on_save = on_save

        self._build_ui()

    def _build_ui(self):
        self.entries = {}

        fields = [
            ("matricule", "Matricule"),
            ("nom", "Nom"),
            ("prenom", "Prénom"),
            ("service", "Service"),
            ("email", "Email"),
            ("telephone", "Téléphone"),
            ("num_permis", "Numéro de permis"),
            ("date_validite_permis", "Validité du permis (YYYY-MM-DD)"),
        ]

        for key, label in fields:
            tk.Label(self, text=label).pack(pady=(10, 0))
            entry = tk.Entry(self)
            entry.pack(fill=tk.X, padx=20)
            self.entries[key] = entry

        self.autorise_var = tk.IntVar(value=0)
        tk.Checkbutton(
            self,
            text="Autorisé à conduire",
            variable=self.autorise_var,
        ).pack(pady=10)

        tk.Button(
            self,
            text="Enregistrer",
            command=self._save,
        ).pack(pady=20)

    def _save(self):
        data = {k: e.get().strip() or None for k, e in self.entries.items()}
        data["autorise_conduire"] = self.autorise_var.get()

        try:
            create_employee(**data)
        except EmployeeError as e:
            messagebox.showerror("Erreur", str(e))
            return

        self.on_save()
        self.destroy()

