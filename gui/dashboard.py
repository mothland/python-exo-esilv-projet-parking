import tkinter as tk
from tkinter import ttk, messagebox

from services.dashboard_service import (
    get_fleet_summary,
    get_available_vehicles,
)

# UI modules
from gui.vehicles import VehicleManagementWindow
from gui.employees import EmployeeManagementWindow
from gui.reservations import ReservationWindow
from gui.alerte_window import AlertsWindow
from gui.maintenance import MaintenanceFuelWindow
from gui.documents import DocumentManagementWindow
from gui.reports import ReportsWindow
from gui.user_management import UserManagementWindow


class DashboardWindow(tk.Toplevel):

    def __init__(self, user: dict, db_path="db/parc_auto.db"):
        super().__init__()

        self.user = user
        self.db_path = db_path

        self.title("Tableau de bord – Parc automobile")
        self.geometry("1000x500")

        self._build_ui()
        self._refresh()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def _build_ui(self):
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        # ================= LEFT: NAVIGATION =================
        nav_frame = ttk.LabelFrame(container, text="Navigation")
        nav_frame.pack(side="left", fill="y", padx=10, pady=10)

        ttk.Button(
            nav_frame,
            text="🚗 Véhicules",
            command=lambda: VehicleManagementWindow(self),
        ).pack(fill="x", pady=2)

        ttk.Button(
            nav_frame,
            text="👤 Employés",
            command=lambda: EmployeeManagementWindow(self),
        ).pack(fill="x", pady=2)

        ttk.Button(
            nav_frame,
            text="📅 Réservations / sorties",
            command=lambda: ReservationWindow(self),
        ).pack(fill="x", pady=2)

        ttk.Button(
            nav_frame,
            text="🛠 Maintenance & carburant",
            command=lambda: MaintenanceFuelWindow(self),
        ).pack(fill="x", pady=2)

        ttk.Button(
            nav_frame,
            text="Alertes & échéances",
            command=lambda: AlertsWindow(self),
        ).pack(fill="x", pady=2)

        ttk.Button(
            nav_frame,
            text="Documents",
            command=lambda: DocumentManagementWindow(self),
        ).pack(fill="x", pady=2)

        ttk.Button(
            nav_frame,
            text="📊 Statistiques",
            command=lambda: ReportsWindow(self),
        ).pack(fill="x", pady=2)

        # Admin-only
        if self.user["role"] == "Admin":
            ttk.Separator(nav_frame).pack(fill="x", pady=5)
            ttk.Button(
                nav_frame,
                text="🔐 Gestion des utilisateurs",
                command=lambda: UserManagementWindow(self.db_path),
            ).pack(fill="x", pady=2)

        # ================= RIGHT: DASHBOARD CONTENT =================
        main_frame = tk.Frame(container)
        main_frame.pack(side="right", fill="both", expand=True)

        # --- Summary frame ---
        self.summary_frame = ttk.LabelFrame(main_frame, text="Résumé du parc")
        self.summary_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_total = ttk.Label(self.summary_frame)
        self.lbl_available = ttk.Label(self.summary_frame)
        self.lbl_sortie = ttk.Label(self.summary_frame)
        self.lbl_maintenance = ttk.Label(self.summary_frame)

        for lbl in (
            self.lbl_total,
            self.lbl_available,
            self.lbl_sortie,
            self.lbl_maintenance,
        ):
            lbl.pack(anchor="w", padx=10, pady=2)

        # --- Alert ---
        self.alert_label = ttk.Label(
            main_frame,
            foreground="red",
            font=("Arial", 11, "bold"),
        )
        self.alert_label.pack(pady=5)

        # --- Available vehicles ---
        self.list_frame = ttk.LabelFrame(main_frame, text="Véhicules disponibles")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("immat", "marque", "modele")
        self.tree = ttk.Treeview(
            self.list_frame,
            columns=columns,
            show="headings",
            height=8,
        )

        self.tree.heading("immat", text="Immatriculation")
        self.tree.heading("marque", text="Marque")
        self.tree.heading("modele", text="Modèle")

        self.tree.pack(fill="both", expand=True)

        ttk.Button(
            main_frame,
            text="🔄 Rafraîchir",
            command=self._refresh,
        ).pack(pady=5)

    # --------------------------------------------------
    # DATA
    # --------------------------------------------------

    def _refresh(self):
        summary = get_fleet_summary(self.db_path)

        self.lbl_total.config(
            text=f"Nombre total de véhicules : {summary['total']}"
        )
        self.lbl_available.config(
            text=f"Disponibles : {summary['available']}"
        )
        self.lbl_sortie.config(
            text=f"En sortie : {summary['en_sortie']}"
        )
        self.lbl_maintenance.config(
            text=f"En maintenance : {summary['maintenance']}"
        )

        if summary["parc_complet"]:
            self.alert_label.config(
                text="Parc complet – Aucun véhicule disponible actuellement"
            )
        else:
            self.alert_label.config(text="")

        # Refresh available vehicles
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in get_available_vehicles(self.db_path):
            self.tree.insert(
                "",
                "end",
                values=(
                    row["immatriculation"],
                    row["marque"],
                    row["modele"],
                ),
            )
