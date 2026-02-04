import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from services.dashboard_service import (
    get_fleet_summary,
    get_vehicle_type_counts,
    get_maintenance_costs_by_vehicle,
)


class ReportsWindow(tk.Toplevel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Statistiques et rapports")
        self.geometry("1200x700")

        self._build_ui()
        self._load_charts()

    # ---------------- UI ----------------

    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(
            top,
            text="🔄 Rafraîchir",
            command=self._load_charts,
        ).pack(side=tk.LEFT)

        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_fleet = tk.Frame(self.notebook)
        self.tab_types = tk.Frame(self.notebook)
        self.tab_maintenance = tk.Frame(self.notebook)

        self.notebook.add(self.tab_fleet, text="État du parc")
        self.notebook.add(self.tab_types, text="Types de véhicules")
        self.notebook.add(self.tab_maintenance, text="Coûts de maintenance")

    # ---------------- Charts ----------------

    def _load_charts(self):
        self._clear_tabs()
        self._fleet_status_chart()
        self._vehicle_types_chart()
        self._maintenance_costs_chart()

    def _clear_tabs(self):
        for tab in (self.tab_fleet, self.tab_types, self.tab_maintenance):
            for w in tab.winfo_children():
                w.destroy()

    # -------- Fleet status --------

    def _fleet_status_chart(self):
        data = get_fleet_summary()

        # Stable mapping (API-safe)
        mapping = [
            ("available", "Disponible", "#4CAF50"),
            ("en_sortie", "En sortie", "#FF9800"),
            ("maintenance", "En maintenance", "#2196F3"),

            # Optional states (only if present)
            ("_panne", "En panne", "#F44336"),
            ("_immobilise", "Immobilisé", "#9E9E9E"),
        ]

        labels = []
        sizes = []
        colors = []

        for key, label, color in mapping:
            if data.get(key, 0) > 0:
                labels.append(label)
                sizes.append(data[key])
                colors.append(color)

        # Safety net: never draw an empty pie
        if not sizes:
            tk.Label(
                self.tab_fleet,
                text="Aucune donnée d'état du parc disponible",
                font=("Arial", 11, "italic"),
            ).pack(pady=20)
            return

        fig = Figure(figsize=(5.5, 4))
        ax = fig.add_subplot(111)

        ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.0f%%",
            startangle=90,
        )
        ax.axis("equal")
        ax.set_title("Répartition de l'état du parc")

        canvas = FigureCanvasTkAgg(fig, self.tab_fleet)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # -------- Vehicle types --------

    def _vehicle_types_chart(self):
        counts = get_vehicle_type_counts()

        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        ax.bar(counts.keys(), counts.values())
        ax.set_title("Véhicules par type")
        ax.set_ylabel("Nombre")

        FigureCanvasTkAgg(fig, self.tab_types).get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # -------- Maintenance costs --------

    def _maintenance_costs_chart(self):
        costs = get_maintenance_costs_by_vehicle()

        if not costs:
            tk.Label(
                self.tab_maintenance,
                text="Aucune donnée de maintenance disponible",
            ).pack(pady=20)
            return

        labels = [c["immatriculation"] for c in costs]
        values = [c["total_cout"] for c in costs]

        fig = Figure(figsize=(7, 4))
        ax = fig.add_subplot(111)
        ax.bar(labels, values)
        ax.set_title("Coût total de maintenance par véhicule")
        ax.set_ylabel("Coût (€)")
        ax.tick_params(axis="x", rotation=45)

        FigureCanvasTkAgg(fig, self.tab_maintenance).get_tk_widget().pack(fill=tk.BOTH, expand=True)
