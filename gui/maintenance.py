import tkinter as tk
from tkinter import ttk, messagebox

from services.maintenance_service import (
    add_maintenance,
    get_all_maintenances,
    MaintenanceError,
)
from services.fuel_service import (
    add_fuel_entry,
    get_all_fuel_entries,
    FuelError,
)
from services.vehicle_service import get_vehicles
from services.employee_service import get_all_employees


class MaintenanceFuelWindow(tk.Toplevel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Maintenance et carburant")
        self.geometry("1200x550")

        self._build_ui()
        self._load_data()

    # ================= UI =================

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.maintenance_tab = tk.Frame(notebook)
        self.fuel_tab = tk.Frame(notebook)

        notebook.add(self.maintenance_tab, text="Maintenance")
        notebook.add(self.fuel_tab, text="Carburant")

        self._build_maintenance_tab()
        self._build_fuel_tab()

    # ================= Maintenance =================

    def _build_maintenance_tab(self):
        top = tk.Frame(self.maintenance_tab)
        top.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(
            top,
            text="➕ Ajouter maintenance",
            command=self._open_add_maintenance,
        ).pack(side=tk.LEFT)

        columns = (
            "vehicule",
            "date",
            "type_intervention",
            "kilometrage",
            "cout",
            "prestataire",
            "date_prochaine_echeance",
        )

        self.maintenance_tree = ttk.Treeview(
            self.maintenance_tab,
            columns=columns,
            show="headings",
        )

        for col in columns:
            self.maintenance_tree.heading(col, text=col.replace("_", " ").title())
            self.maintenance_tree.column(col, width=160)

        self.maintenance_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ================= Fuel =================

    def _build_fuel_tab(self):
        top = tk.Frame(self.fuel_tab)
        top.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(
            top,
            text="➕ Ajouter ravitaillement",
            command=self._open_add_fuel,
        ).pack(side=tk.LEFT)

        # ✅ AJOUT DE LA COLONNE consommation
        columns = (
            "vehicule",
            "employe",
            "date",
            "quantite_litres",
            "cout",
            "kilometrage",
            "consommation",
        )

        self.fuel_tree = ttk.Treeview(
            self.fuel_tab,
            columns=columns,
            show="headings",
        )

        for col in columns:
            self.fuel_tree.heading(col, text=col.replace("_", " ").title())
            self.fuel_tree.column(col, width=160)

        self.fuel_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ================= Data =================

    def _load_data(self):
        self._load_maintenances()
        self._load_fuel_entries()

    def _load_maintenances(self):
        self.maintenance_tree.delete(*self.maintenance_tree.get_children())
        for m in get_all_maintenances():
            self.maintenance_tree.insert(
                "",
                tk.END,
                values=(
                    m["immatriculation"],
                    m["date"],
                    m["type_intervention"],
                    m["kilometrage"],
                    m["cout"],
                    m["prestataire"],
                    m["date_prochaine_echeance"],
                ),
            )

    def _load_fuel_entries(self):
        self.fuel_tree.delete(*self.fuel_tree.get_children())
        for f in get_all_fuel_entries():
            self.fuel_tree.insert(
                "",
                tk.END,
                values=(
                    f["immatriculation"],
                    f["prenom"] + " " + f["nom"],
                    f["date"],
                    f["quantite_litres"],
                    f["cout"],
                    f["kilometrage"],
                    f["consommation"],  # ✅ AFFICHAGE CONSO
                ),
            )

    # ================= Actions =================

    def _open_add_maintenance(self):
        AddMaintenanceWindow(self, on_save=self._load_maintenances)

    def _open_add_fuel(self):
        AddFuelWindow(self, on_save=self._load_fuel_entries)


# =========================================================
# Add Maintenance Popup
# =========================================================

class AddMaintenanceWindow(tk.Toplevel):

    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Ajouter une maintenance")
        self.geometry("400x500")
        self.on_save = on_save

        self._build_ui()

    def _build_ui(self):
        self.entries = {}

        tk.Label(self, text="Véhicule").pack(pady=(10, 0))
        vehicles = get_vehicles()
        self.vehicle_var = tk.StringVar()
        self.vehicle_map = {v["immatriculation"]: v["id"] for v in vehicles}

        ttk.Combobox(
            self,
            textvariable=self.vehicle_var,
            values=list(self.vehicle_map.keys()),
            state="readonly",
        ).pack(fill=tk.X, padx=20)

        fields = [
            ("date", "Date (YYYY-MM-DD)"),
            ("type_intervention", "Type d'intervention"),
            ("kilometrage", "Kilométrage"),
            ("cout", "Coût"),
            ("prestataire", "Prestataire"),
            ("date_prochaine_echeance", "Prochaine échéance"),
        ]

        for key, label in fields:
            tk.Label(self, text=label).pack(pady=(10, 0))
            e = tk.Entry(self)
            e.pack(fill=tk.X, padx=20)
            self.entries[key] = e

        tk.Button(self, text="Enregistrer", command=self._save).pack(pady=20)

    def _save(self):
        try:
            vehicule_id = self.vehicle_map[self.vehicle_var.get()]
            data = {k: v.get().strip() or None for k, v in self.entries.items()}
            add_maintenance(vehicule_id=vehicule_id, **data)
        except (KeyError, MaintenanceError) as e:
            messagebox.showerror("Erreur", str(e))
            return

        self.on_save()
        self.destroy()


# =========================================================
# Add Fuel Popup (MODIFIÉ PROPREMENT)
# =========================================================

class AddFuelWindow(tk.Toplevel):

    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Ajouter un ravitaillement")
        self.geometry("400x500")
        self.on_save = on_save

        self._build_ui()

    def _build_ui(self):
        self.entries = {}

        tk.Label(self, text="Véhicule").pack(pady=(10, 0))
        vehicles = get_vehicles()
        self.vehicle_var = tk.StringVar()
        self.vehicle_map = {v["immatriculation"]: v["id"] for v in vehicles}

        ttk.Combobox(
            self,
            textvariable=self.vehicle_var,
            values=list(self.vehicle_map.keys()),
            state="readonly",
        ).pack(fill=tk.X, padx=20)

        tk.Label(self, text="Employé").pack(pady=(10, 0))
        employees = get_all_employees()
        self.employee_var = tk.StringVar()
        self.employee_map = {f'{e["prenom"]} {e["nom"]}': e["id"] for e in employees}

        ttk.Combobox(
            self,
            textvariable=self.employee_var,
            values=list(self.employee_map.keys()),
            state="readonly",
        ).pack(fill=tk.X, padx=20)

        fields = [
            ("date", "Date (YYYY-MM-DD)"),
            ("quantite_litres", "Quantité (L)"),
            ("cout", "Coût"),
            ("kilometrage", "Kilométrage"),
            ("station", "Station"),
        ]

        for key, label in fields:
            tk.Label(self, text=label).pack(pady=(10, 0))
            e = tk.Entry(self)
            e.pack(fill=tk.X, padx=20)
            self.entries[key] = e

        tk.Button(self, text="Enregistrer", command=self._save).pack(pady=20)

    def _save(self):
        try:
            vehicule_id = self.vehicle_map[self.vehicle_var.get()]
            employe_id = self.employee_map[self.employee_var.get()]

            add_fuel_entry(
                vehicule_id=vehicule_id,
                employe_id=employe_id,
                date=self.entries["date"].get(),
                quantite_litres=float(self.entries["quantite_litres"].get()),
                cout=float(self.entries["cout"].get()),
                kilometrage=int(self.entries["kilometrage"].get())
                if self.entries["kilometrage"].get()
                else None,
                station=self.entries["station"].get() or None,
            )

        except (ValueError, KeyError, FuelError) as e:
            messagebox.showerror("Erreur", str(e))
            return

        self.on_save()
        self.destroy()