import tkinter as tk
from tkinter import ttk, messagebox

from services.document_service import (
    add_document,
    get_documents_for_vehicle,
    DocumentError,
)
from services.vehicle_service import get_vehicles


class DocumentManagementWindow(tk.Toplevel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Documents administratifs")
        self.geometry("1000x500")

        self._build_ui()
        self._load_documents()  # Charger tous les documents au démarrage

    # ---------------- UI ----------------

    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top, text="Filtrer par véhicule").pack(side=tk.LEFT)
        self.vehicles = get_vehicles()
        self.vehicle_var = tk.StringVar()
        
        # Option "Tous les véhicules" + liste des véhicules
        self.vehicle_map = {"Tous les véhicules": None}
        self.vehicle_map.update({
            f'{v["immatriculation"]} - {v["marque"]} {v["modele"]}': v["id"]
            for v in self.vehicles
        })

        self.vehicle_combo = ttk.Combobox(
            top,
            textvariable=self.vehicle_var,
            values=list(self.vehicle_map.keys()),
            state="readonly",
            width=40,
        )
        self.vehicle_combo.pack(side=tk.LEFT, padx=5)
        self.vehicle_combo.set("Tous les véhicules")  # Valeur par défaut
        self.vehicle_combo.bind("<<ComboboxSelected>>", self._load_documents)

        tk.Button(
            top,
            text="➕ Ajouter document",
            command=self._open_add_document,
        ).pack(side=tk.LEFT, padx=10)

        columns = (
            "vehicule",
            "type_document",
            "date_emission",
            "date_echeance",
            "chemin_fichier",
            "description",
        )

        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
        )

        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=150 if col == "vehicule" else 140)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ---------------- Data ----------------

    def _load_documents(self, event=None):
        self.tree.delete(*self.tree.get_children())

        label = self.vehicle_var.get()
        if not label:
            label = "Tous les véhicules"
            self.vehicle_combo.set(label)

        vehicule_id = self.vehicle_map.get(label)
        
        # Si "Tous les véhicules" est sélectionné (vehicule_id = None)
        if vehicule_id is None:
            # Charger les documents de tous les véhicules
            for v in self.vehicles:
                docs = get_documents_for_vehicle(v["id"])
                vehicle_label = f'{v["immatriculation"]} - {v["marque"]} {v["modele"]}'
                
                for d in docs:
                    self.tree.insert(
                        "",
                        tk.END,
                        values=(
                            vehicle_label,
                            d["type_document"],
                            d["date_emission"],
                            d["date_echeance"],
                            d["chemin_fichier"],
                            d["description"],
                        ),
                    )
        else:
            # Charger les documents d'un véhicule spécifique
            docs = get_documents_for_vehicle(vehicule_id)
            vehicle_label = label
            
            for d in docs:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        vehicle_label,
                        d["type_document"],
                        d["date_emission"],
                        d["date_echeance"],
                        d["chemin_fichier"],
                        d["description"],
                    ),
                )

    # ---------------- Actions ----------------

    def _open_add_document(self):
        # Si "Tous les véhicules" est sélectionné, demander de choisir un véhicule spécifique
        label = self.vehicle_var.get()
        if not label or label == "Tous les véhicules":
            messagebox.showwarning(
                "Attention",
                "Veuillez sélectionner un véhicule spécifique pour ajouter un document",
            )
            return

        vehicule_id = self.vehicle_map[label]
        AddDocumentWindow(self, vehicule_id, on_save=self._load_documents)


# =========================================================
# Add Document Popup
# =========================================================

class AddDocumentWindow(tk.Toplevel):

    def __init__(self, parent, vehicule_id, on_save):
        super().__init__(parent)
        self.title("Ajouter un document")
        self.geometry("400x450")
        self.vehicule_id = vehicule_id
        self.on_save = on_save

        self._build_ui()

    def _build_ui(self):
        self.entries = {}

        fields = [
            ("type_document", "Type de document"),
            ("date_emission", "Date d'émission (YYYY-MM-DD)"),
            ("date_echeance", "Date d'échéance (YYYY-MM-DD)"),
            ("chemin_fichier", "Chemin du fichier"),
            ("description", "Description"),
        ]

        for key, label in fields:
            tk.Label(self, text=label).pack(pady=(10, 0))
            entry = tk.Entry(self)
            entry.pack(fill=tk.X, padx=20)
            self.entries[key] = entry

        tk.Button(
            self,
            text="Enregistrer",
            command=self._save,
        ).pack(pady=20)

    def _save(self):
        data = {k: e.get().strip() or None for k, e in self.entries.items()}

        try:
            add_document(
                vehicule_id=self.vehicule_id,
                **data,
            )
        except DocumentError as e:
            messagebox.showerror("Erreur", str(e))
            return

        self.on_save()
        self.destroy()