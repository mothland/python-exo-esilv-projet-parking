import tkinter as tk
from tkinter import ttk, messagebox

from services.vehicle_service import (
    get_vehicles,
    create_vehicle,
    VehicleError,
)


STATUS_COLORS = {
    "disponible": "#d4edda",    # green
    "en_sortie": "#fff3cd",     # orange
    "en_maintenance": "#f8d7da" # red
}


class VehicleManagementWindow(tk.Toplevel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Gestion des véhicules")
        self.geometry("1000x500")

        self._build_ui()
        self._load_vehicles()

    # ---------------- UI ----------------

    def _build_ui(self):
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(
            top_frame,
            text="➕ Ajouter un véhicule",
            command=self._open_add_vehicle
        ).pack(side=tk.LEFT)

        tk.Button(
            top_frame,
            text="🔄 Rafraîchir",
            command=self._load_vehicles
        ).pack(side=tk.LEFT, padx=5)

        columns = (
            "immatriculation",
            "marque",
            "modele",
            "type_vehicule",
            "type_affectation",
            "statut",
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

        # Status row coloring
        for status, color in STATUS_COLORS.items():
            self.tree.tag_configure(status, background=color)

    # ---------------- Data ----------------

    def _load_vehicles(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        vehicles = get_vehicles()

        for v in vehicles:
            status = v["statut"]
            self.tree.insert(
                "",
                tk.END,
                values=(
                    v["immatriculation"],
                    v["marque"],
                    v["modele"],
                    v["type_vehicule"],
                    v["type_affectation"],
                    status,
                ),
                tags=(status,),
            )

    # ---------------- Actions ----------------

    def _open_add_vehicle(self):
        AddVehicleWindow(self, on_save=self._load_vehicles)


# =========================================================
# Add Vehicle Popup
# =========================================================

class AddVehicleWindow(tk.Toplevel):

    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Ajouter un véhicule")
        self.geometry("400x450")
        self.on_save = on_save

        self._build_ui()

    def _build_ui(self):
        self.entries = {}

        fields = [
            ("immatriculation", "Immatriculation"),
            ("marque", "Marque"),
            ("modele", "Modèle"),
            ("type_vehicule", "Type de véhicule"),
            ("type_affectation", "Type d'affectation"),
        ]

        for key, label in fields:
            tk.Label(self, text=label).pack(pady=(10, 0))
            entry = tk.Entry(self)
            entry.pack(fill=tk.X, padx=20)
            self.entries[key] = entry

        tk.Label(self, text="Statut").pack(pady=(10, 0))
        self.statut_var = tk.StringVar(value="disponible")
        ttk.Combobox(
            self,
            textvariable=self.statut_var,
            values=["disponible", "en_sortie", "en_maintenance"],
            state="readonly",
        ).pack(fill=tk.X, padx=20)

        tk.Button(
            self,
            text="Enregistrer",
            command=self._save,
        ).pack(pady=20)

    def _save(self):
        data = {k: e.get().strip() for k, e in self.entries.items()}
        data["statut"] = self.statut_var.get()

        try:
            create_vehicle(**data)
        except VehicleError as e:
            messagebox.showerror("Erreur", str(e))
            return

        self.on_save()
        self.destroy()
