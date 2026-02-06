import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, datetime

from services.reservation_service import (
    get_all_reservations,
    create_reservation,
    return_vehicle,
    ReservationError,
)
from services.vehicle_service import get_available_vehicles
from services.employee_service import get_all_employees


# =========================================================
# MAIN WINDOW
# =========================================================

class ReservationWindow(tk.Toplevel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Réservations et sorties de véhicules")
        self.geometry("1100x500")

        self._build_ui()
        self._load_reservations()

    # ---------------- UI ----------------

    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(
            top,
            text="➕ Nouvelle réservation / sortie",
            command=self._open_add_reservation,
        ).pack(side=tk.LEFT)

        tk.Button(
            top,
            text="🔄 Rafraîchir",
            command=self._load_reservations,
        ).pack(side=tk.LEFT, padx=5)

        columns = (
            "vehicule",
            "employe",
            "date_sortie",
            "date_retour_prevue",
            "statut",
        )

        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=180)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Button(
            self,
            text="↩️ Enregistrer retour du véhicule sélectionné",
            command=self._return_selected,
        ).pack(pady=5)

    # ---------------- Data ----------------

    def _load_reservations(self):
        self.tree.delete(*self.tree.get_children())

        reservations = get_all_reservations()

        for r in reservations:
            self.tree.insert(
                "",
                tk.END,
                iid=r["id"],
                values=(
                    r["immatriculation"],
                    f'{r["prenom"]} {r["nom"]}',
                    r["date_sortie_reelle"] or r["date_sortie_prevue"],
                    r["date_retour_prevue"],
                    r["statut"],
                ),
            )

    # ---------------- Actions ----------------

    def _open_add_reservation(self):
        AddReservationWindow(self, on_save=self._load_reservations)

    def _return_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Aucune réservation sélectionnée")
            return

        reservation_id = int(selected[0])

        km_retour = simpledialog.askinteger(
            "Retour véhicule",
            "Entrez le kilométrage au retour :",
            parent=self,
            minvalue=0
        )

        if km_retour is None:
            return

        etat = simpledialog.askstring(
            "État du véhicule",
            "État du véhicule (propre / sale / endommage) :",
            parent=self
        )

        if not etat:
            messagebox.showerror("Erreur", "État du véhicule obligatoire")
            return

        carburant = simpledialog.askstring(
            "Carburant",
            "Niveau de carburant au retour :",
            parent=self
        )

        try:
            return_vehicle(
                reservation_id=reservation_id,
                km_retour=km_retour,
                etat_retour=etat.lower(),
                niveau_carburant=carburant,
            )
        except ReservationError as e:
            messagebox.showerror("Erreur", str(e))
            return

        messagebox.showinfo("Succès", "Retour du véhicule enregistré")
        self._load_reservations()


# =========================================================
# ADD RESERVATION WINDOW
# =========================================================

class AddReservationWindow(tk.Toplevel):

    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Nouvelle réservation / sortie")
        self.geometry("420x650")
        self.on_save = on_save

        self._build_ui()

    def _build_ui(self):

        # Véhicule
        tk.Label(self, text="Véhicule").pack(pady=(10, 0))
        self.vehicles = get_available_vehicles()
        self.vehicle_var = tk.StringVar()
        self.vehicle_map = {
            f'{v["immatriculation"]} - {v["marque"]} {v["modele"]}': v["id"]
            for v in self.vehicles
        }
        ttk.Combobox(
            self,
            textvariable=self.vehicle_var,
            values=list(self.vehicle_map.keys()),
            state="readonly",
        ).pack(fill=tk.X, padx=20)

        # Employé
        tk.Label(self, text="Employé").pack(pady=(10, 0))
        self.employees = get_all_employees()
        self.employee_var = tk.StringVar()
        self.employee_map = {
            f'{e["prenom"]} {e["nom"]} ({e["matricule"]})': e["id"]
            for e in self.employees
        }
        ttk.Combobox(
            self,
            textvariable=self.employee_var,
            values=list(self.employee_map.keys()),
            state="readonly",
        ).pack(fill=tk.X, padx=20)

        # ================= SORTIE =================
        tk.Label(self, text="Date sortie prévue (YYYY-MM-DD)").pack(pady=(10, 0))
        self.date_sortie_entry = tk.Entry(self)
        self.date_sortie_entry.insert(0, date.today().isoformat())
        self.date_sortie_entry.pack(fill=tk.X, padx=20)

        tk.Label(self, text="Heure sortie prévue (HH:MM)").pack(pady=(10, 0))
        self.heure_sortie_entry = tk.Entry(self)
        self.heure_sortie_entry.pack(fill=tk.X, padx=20)

        # ================= RETOUR =================
        tk.Label(self, text="Date retour prévue (YYYY-MM-DD)").pack(pady=(10, 0))
        self.date_retour_entry = tk.Entry(self)
        self.date_retour_entry.pack(fill=tk.X, padx=20)

        tk.Label(self, text="Heure retour prévue (HH:MM)").pack(pady=(10, 0))
        self.heure_retour_entry = tk.Entry(self)
        self.heure_retour_entry.pack(fill=tk.X, padx=20)

        # Kilométrage départ
        tk.Label(self, text="Kilométrage départ").pack(pady=(10, 0))
        self.km_depart_entry = tk.Entry(self)
        self.km_depart_entry.pack(fill=tk.X, padx=20)

        # Motif
        tk.Label(self, text="Motif").pack(pady=(10, 0))
        self.motif_entry = tk.Entry(self)
        self.motif_entry.pack(fill=tk.X, padx=20)

        # Destination
        tk.Label(self, text="Destination").pack(pady=(10, 0))
        self.destination_entry = tk.Entry(self)
        self.destination_entry.pack(fill=tk.X, padx=20)

        tk.Button(self, text="Enregistrer", command=self._save).pack(pady=20)

    def _save(self):
        try:
            vehicule_id = self.vehicle_map[self.vehicle_var.get()]
            employe_id = self.employee_map[self.employee_var.get()]
            km_depart = int(self.km_depart_entry.get())
        except (KeyError, ValueError):
            messagebox.showerror("Erreur", "Données invalides")
            return

        motif = self.motif_entry.get().strip()
        destination = self.destination_entry.get().strip()

        if not motif or not destination:
            messagebox.showerror("Erreur", "Motif et destination obligatoires")
            return

        if not self.date_sortie_entry.get().strip() or not self.date_retour_entry.get().strip():
            messagebox.showerror("Erreur", "Dates sortie et retour obligatoires")
            return

        # 🔒 Vérification sortie < retour
        try:
            sortie_dt = datetime.strptime(
                self.date_sortie_entry.get() + " " + self.heure_sortie_entry.get(),
                "%Y-%m-%d %H:%M"
            )
            retour_dt = datetime.strptime(
                self.date_retour_entry.get() + " " + self.heure_retour_entry.get(),
                "%Y-%m-%d %H:%M"
            )
            if retour_dt <= sortie_dt:
                messagebox.showerror("Erreur", "La date de retour doit être après la sortie")
                return
        except ValueError:
            messagebox.showerror("Erreur", "Format date ou heure invalide")
            return

        try:
            create_reservation(
                vehicule_id=vehicule_id,
                employe_id=employe_id,
                date_sortie_prevue=self.date_sortie_entry.get(),
                heure_sortie_prevue=self.heure_sortie_entry.get(),
                date_retour_prevue=self.date_retour_entry.get(),
                heure_retour_prevue=self.heure_retour_entry.get(),
                km_depart=km_depart,
                motif=motif,
                destination=destination,
            )
        except ReservationError as e:
            messagebox.showerror("Erreur", str(e))
            return

        self.on_save()
        self.destroy()