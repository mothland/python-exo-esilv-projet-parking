import tkinter as tk
from tkinter import ttk

from services.alert_service import (
    get_document_alerts,
    get_maintenance_alerts,
)


class AlertsWindow(tk.Toplevel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Alertes & échéances")
        self.geometry("1000x500")

        self._build_ui()
        self._load_alerts()

    # ================= UI =================

    def _build_ui(self):
        tk.Label(
            self,
            text="Échéances proches (< 30 jours) et dépassées",
            font=("Arial", 14, "bold"),
        ).pack(pady=10)

        columns = ("type", "vehicule", "libelle", "date_echeance", "statut")

        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
        )

        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=180)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 🎨 COULEURS VISUELLES
        self.tree.tag_configure("retard", background="#ffb3b3")   # rouge
        self.tree.tag_configure("proche", background="#ffe0b3")   # orange

    # ================= DATA =================

    def _load_alerts(self):
        self.tree.delete(*self.tree.get_children())

        alerts = []
        alerts.extend(get_document_alerts())
        alerts.extend(get_maintenance_alerts())

        for a in alerts:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    a["type"],
                    a["vehicule"],
                    a["libelle"],
                    a["date_echeance"],
                    a["statut"],
                ),
                tags=(a["statut"],),
            )