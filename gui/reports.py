import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from services.dashboard_service import (
    get_fleet_summary,
    get_vehicle_type_counts,
    get_maintenance_costs_by_vehicle,
    get_total_mileage,
    get_mileage_by_vehicle,
    get_mileage_by_period,
    get_detailed_costs_by_vehicle,
    get_vehicle_utilization_rate,
    get_most_active_employees,
    get_average_consumption_by_vehicle,
    get_average_consumption_by_type,
    get_cost_evolution,
    export_to_csv,
    export_fleet_summary_to_pdf,
)


class ReportsWindow(tk.Toplevel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Statistiques et rapports")
        self.geometry("1400x800")

        self._build_ui()
        self._load_charts()

    # ---------------- UI ----------------

    def _build_ui(self):
        # Barre d'outils en haut
        toolbar = tk.Frame(self, bg='#f0f0f0')
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(
            toolbar,
            text="🔄 Rafraîchir",
            command=self._load_charts,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            toolbar,
            text="📊 Export CSV",
            command=self._export_csv_menu,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            toolbar,
            text="📄 Export PDF",
            command=self._export_pdf_menu,
            bg='#FF5722',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_fleet = tk.Frame(self.notebook)
        self.tab_mileage = tk.Frame(self.notebook)
        self.tab_costs = tk.Frame(self.notebook)
        self.tab_utilization = tk.Frame(self.notebook)
        self.tab_employees = tk.Frame(self.notebook)
        self.tab_consumption = tk.Frame(self.notebook)
        self.tab_evolution = tk.Frame(self.notebook)

        self.notebook.add(self.tab_fleet, text="📊 État du parc")
        self.notebook.add(self.tab_mileage, text="🛣️ Kilométrage")
        self.notebook.add(self.tab_costs, text="💰 Coûts détaillés")
        self.notebook.add(self.tab_utilization, text="📈 Taux d'utilisation")
        self.notebook.add(self.tab_employees, text="👥 Employés actifs")
        self.notebook.add(self.tab_consumption, text="⛽ Consommation")
        self.notebook.add(self.tab_evolution, text="📉 Évolution")

    # ---------------- Charts ----------------

    def _load_charts(self):
        self._clear_tabs()
        
        # Onglet 1 : État du parc
        self._fleet_status_chart()
        self._vehicle_types_chart()
        
        # Onglet 2 : Kilométrage
        self._mileage_charts()
        
        # Onglet 3 : Coûts détaillés
        self._detailed_costs_chart()
        
        # Onglet 4 : Taux d'utilisation
        self._utilization_chart()
        
        # Onglet 5 : Employés actifs
        self._employees_activity_chart()
        
        # Onglet 6 : Consommation
        self._consumption_charts()
        
        # Onglet 7 : Évolution
        self._cost_evolution_chart()

    def _clear_tabs(self):
        for tab in (self.tab_fleet, self.tab_mileage, self.tab_costs,
                    self.tab_utilization, self.tab_employees, 
                    self.tab_consumption, self.tab_evolution):
            for w in tab.winfo_children():
                w.destroy()

    # -------- Fleet status --------

    def _fleet_status_chart(self):
        data = get_fleet_summary()

        # Container pour les deux graphiques côte à côte
        container = tk.Frame(self.tab_fleet)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Cadre gauche : État du parc
        left_frame = tk.Frame(container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

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
                left_frame,
                text="Aucune donnée d'état du parc disponible",
                font=("Arial", 11, "italic"),
            ).pack(pady=20)
            return

        fig = Figure(figsize=(6, 5))
        ax = fig.add_subplot(111)

        ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.axis("equal")
        ax.set_title("Répartition de l'état du parc", fontsize=14, fontweight='bold')

        canvas = FigureCanvasTkAgg(fig, left_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # -------- Vehicle types --------

    def _vehicle_types_chart(self):
        counts = get_vehicle_type_counts()

        # Cadre droit : Types de véhicules
        right_frame = tk.Frame(self.tab_fleet)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        if not counts:
            tk.Label(
                right_frame,
                text="Aucune donnée de type de véhicule",
            ).pack(pady=20)
            return

        fig = Figure(figsize=(6, 5))
        ax = fig.add_subplot(111)
        
        types = list(counts.keys())
        values = list(counts.values())
        
        bars = ax.bar(types, values, color='#2196F3')
        ax.set_title("Véhicules par type", fontsize=14, fontweight='bold')
        ax.set_ylabel("Nombre")
        
        if len(types) > 3:
            ax.tick_params(axis='x', rotation=45)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom')

        canvas = FigureCanvasTkAgg(fig, right_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # -------- Mileage --------

    def _mileage_charts(self):
        mileage_data = get_mileage_by_vehicle()
        
        if not mileage_data:
            tk.Label(
                self.tab_mileage,
                text="Aucune donnée de kilométrage disponible",
                font=('Arial', 12)
            ).pack(pady=50)
            return
        
        # Top 10 véhicules par kilométrage
        top_10 = mileage_data[:10]
        
        fig = Figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        labels = [f"{v['immatriculation']}\n{v['marque']} {v['modele']}" for v in top_10]
        km = [v['kilometrage'] for v in top_10]
        
        bars = ax.barh(labels, km, color='#FF9800')
        ax.set_xlabel('Kilométrage (km)', fontsize=12)
        ax.set_title('Top 10 - Kilométrage par véhicule', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{int(width):,} km',
                   ha='left', va='center', fontsize=9)
        
        canvas = FigureCanvasTkAgg(fig, self.tab_mileage)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # -------- Detailed costs --------

    def _detailed_costs_chart(self):
        costs_data = get_detailed_costs_by_vehicle()
        
        if not costs_data:
            tk.Label(
                self.tab_costs,
                text="Aucune donnée de coûts disponible",
                font=('Arial', 12)
            ).pack(pady=50)
            return
        
        # Top 10 véhicules par coût total
        top_10 = [c for c in costs_data if c['cout_total'] > 0][:10]
        
        if not top_10:
            tk.Label(
                self.tab_costs,
                text="Aucun coût enregistré",
                font=('Arial', 12)
            ).pack(pady=50)
            return
        
        fig = Figure(figsize=(12, 7))
        ax = fig.add_subplot(111)
        
        labels = [f"{v['immatriculation']}" for v in top_10]
        carburant = [v['cout_carburant'] for v in top_10]
        maintenance = [v['cout_maintenance'] for v in top_10]
        assurance = [v['cout_assurance'] for v in top_10]
        
        x = range(len(labels))
        width = 0.25
        
        ax.bar([i - width for i in x], carburant, width, label='Carburant', color='#FF5722')
        ax.bar(x, maintenance, width, label='Maintenance', color='#2196F3')
        ax.bar([i + width for i in x], assurance, width, label='Assurance', color='#4CAF50')
        
        ax.set_ylabel('Coût (€)', fontsize=12)
        ax.set_title('Coûts détaillés par véhicule (Top 10)', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, self.tab_costs)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # -------- Utilization --------

    def _utilization_chart(self):
        util_data = get_vehicle_utilization_rate()
        
        if not util_data:
            tk.Label(
                self.tab_utilization,
                text="Aucune donnée d'utilisation disponible",
                font=('Arial', 12)
            ).pack(pady=50)
            return
        
        # Filtrer les véhicules avec utilisation > 0
        active_vehicles = [v for v in util_data if v['taux_utilisation'] > 0][:15]
        
        if not active_vehicles:
            tk.Label(
                self.tab_utilization,
                text="Aucun véhicule utilisé dans les 30 derniers jours",
                font=('Arial', 12)
            ).pack(pady=50)
            return
        
        fig = Figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        labels = [v['immatriculation'] for v in active_vehicles]
        taux = [v['taux_utilisation'] for v in active_vehicles]
        
        # Couleurs selon le taux
        colors = []
        for t in taux:
            if t >= 70:
                colors.append('#4CAF50')  # Vert : très utilisé
            elif t >= 40:
                colors.append('#FF9800')  # Orange : moyennement utilisé
            else:
                colors.append('#F44336')  # Rouge : peu utilisé
        
        bars = ax.bar(labels, taux, color=colors)
        ax.set_ylabel('Taux d\'utilisation (%)', fontsize=12)
        ax.set_xlabel('Véhicule', fontsize=12)
        ax.set_title('Taux d\'utilisation des véhicules (30 derniers jours)', 
                     fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', alpha=0.3)
        ax.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='Seuil 50%')
        ax.legend()
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=8)
        
        canvas = FigureCanvasTkAgg(fig, self.tab_utilization)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # -------- Employees --------

    def _employees_activity_chart(self):
        emp_data = get_most_active_employees()
        
        if not emp_data:
            tk.Label(
                self.tab_employees,
                text="Aucune donnée d'activité d'employés disponible",
                font=('Arial', 12)
            ).pack(pady=50)
            return
        
        top_15 = emp_data[:15]
        
        # Créer deux sous-graphiques
        fig = Figure(figsize=(14, 10))
        
        # Graphique 1 : Nombre de sorties
        ax1 = fig.add_subplot(211)
        labels1 = [f"{e['nom']} {e['prenom']}" for e in top_15]
        sorties = [e['nombre_sorties'] for e in top_15]
        
        bars1 = ax1.barh(labels1, sorties, color='#2196F3')
        ax1.set_xlabel('Nombre de sorties', fontsize=12)
        ax1.set_title('Top 15 - Employés par nombre de sorties', fontsize=14, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        for bar in bars1:
            width = bar.get_width()
            ax1.text(width, bar.get_y() + bar.get_height()/2.,
                    f' {int(width)}',
                    ha='left', va='center', fontsize=9)
        
        # Graphique 2 : Kilomètres parcourus
        ax2 = fig.add_subplot(212)
        labels2 = [f"{e['nom']} {e['prenom']}" for e in top_15]
        km_total = [e['km_total'] for e in top_15]
        
        bars2 = ax2.barh(labels2, km_total, color='#FF9800')
        ax2.set_xlabel('Kilomètres parcourus', fontsize=12)
        ax2.set_title('Top 15 - Employés par kilomètres parcourus', fontsize=14, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        for bar in bars2:
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2.,
                    f' {int(width):,} km',
                    ha='left', va='center', fontsize=9)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.tab_employees)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # -------- Consumption --------

    def _consumption_charts(self):
        consumption_by_type = get_average_consumption_by_type()
        
        if not consumption_by_type:
            tk.Label(
                self.tab_consumption,
                text="Aucune donnée de consommation disponible",
                font=('Arial', 12)
            ).pack(pady=50)
            return
        
        fig = Figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        types = [c['type_vehicule'] for c in consumption_by_type]
        km_moyen = [c['km_moyen_vehicule'] for c in consumption_by_type]
        
        bars = ax.bar(types, km_moyen, color='#4CAF50')
        ax.set_ylabel('Kilométrage moyen (km)', fontsize=12)
        ax.set_xlabel('Type de véhicule', fontsize=12)
        ax.set_title('Kilométrage moyen par type de véhicule', fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height):,}',
                   ha='center', va='bottom')
        
        canvas = FigureCanvasTkAgg(fig, self.tab_consumption)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # -------- Evolution --------

    def _cost_evolution_chart(self):
        evolution_data = get_cost_evolution(months=12)
        
        if not evolution_data:
            tk.Label(
                self.tab_evolution,
                text="Aucune donnée d'évolution disponible",
                font=('Arial', 12)
            ).pack(pady=50)
            return
        
        fig = Figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        periodes = [e['periode'] for e in evolution_data]
        carburant = [e['cout_carburant'] for e in evolution_data]
        maintenance = [e['cout_maintenance'] for e in evolution_data]
        total = [e['cout_total'] for e in evolution_data]
        
        ax.plot(periodes, carburant, marker='o', label='Carburant', color='#FF5722', linewidth=2)
        ax.plot(periodes, maintenance, marker='s', label='Maintenance', color='#2196F3', linewidth=2)
        ax.plot(periodes, total, marker='^', label='Total', color='#4CAF50', linewidth=2, linestyle='--')
        
        ax.set_ylabel('Coût (€)', fontsize=12)
        ax.set_xlabel('Période', fontsize=12)
        ax.set_title('Évolution des coûts sur 12 mois', fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, self.tab_evolution)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # -------- Export CSV --------

    def _export_csv_menu(self):
        menu_window = tk.Toplevel(self)
        menu_window.title("Export CSV")
        menu_window.geometry("400x400")
        
        tk.Label(
            menu_window,
            text="Sélectionnez le rapport à exporter",
            font=('Arial', 12, 'bold')
        ).pack(pady=10)
        
        options = [
            ("Kilométrage par véhicule", self._export_mileage_csv),
            ("Coûts détaillés", self._export_costs_csv),
            ("Taux d'utilisation", self._export_utilization_csv),
            ("Employés actifs", self._export_employees_csv),
            ("Consommation par type", self._export_consumption_csv),
        ]
        
        for text, command in options:
            tk.Button(
                menu_window,
                text=text,
                command=lambda c=command, w=menu_window: [c(), w.destroy()],
                width=30,
                pady=5
            ).pack(pady=5)
        
        tk.Button(
            menu_window,
            text="Annuler",
            command=menu_window.destroy,
            bg='#f44336',
            fg='white'
        ).pack(pady=20)

    def _export_mileage_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"kilometrage_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if filename:
            data = get_mileage_by_vehicle()
            headers = ['immatriculation', 'marque', 'modele', 'type_vehicule', 'kilometrage']
            success, msg = export_to_csv(data, headers, filename)
            if success:
                messagebox.showinfo("Succès", msg)
            else:
                messagebox.showerror("Erreur", msg)

    def _export_costs_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"couts_detailles_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if filename:
            data = get_detailed_costs_by_vehicle()
            headers = ['immatriculation', 'marque', 'modele', 'cout_carburant', 
                      'cout_maintenance', 'cout_assurance', 'cout_total']
            success, msg = export_to_csv(data, headers, filename)
            if success:
                messagebox.showinfo("Succès", msg)
            else:
                messagebox.showerror("Erreur", msg)

    def _export_utilization_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"taux_utilisation_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if filename:
            data = get_vehicle_utilization_rate()
            headers = ['immatriculation', 'marque', 'modele', 'statut', 
                      'jours_utilises', 'nombre_sorties', 'km_parcourus', 'taux_utilisation']
            success, msg = export_to_csv(data, headers, filename)
            if success:
                messagebox.showinfo("Succès", msg)
            else:
                messagebox.showerror("Erreur", msg)

    def _export_employees_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"employes_actifs_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if filename:
            data = get_most_active_employees()
            headers = ['nom', 'prenom', 'service', 'nombre_sorties', 
                      'km_total', 'km_moyen_par_sortie']
            success, msg = export_to_csv(data, headers, filename)
            if success:
                messagebox.showinfo("Succès", msg)
            else:
                messagebox.showerror("Erreur", msg)

    def _export_consumption_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"consommation_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if filename:
            data = get_average_consumption_by_type()
            headers = ['type_vehicule', 'nombre_vehicules', 'km_total', 
                      'cout_carburant_total', 'km_moyen_vehicule']
            success, msg = export_to_csv(data, headers, filename)
            if success:
                messagebox.showinfo("Succès", msg)
            else:
                messagebox.showerror("Erreur", msg)

    # -------- Export PDF --------

    def _export_pdf_menu(self):
        menu_window = tk.Toplevel(self)
        menu_window.title("Export PDF")
        menu_window.geometry("400x250")
        
        tk.Label(
            menu_window,
            text="Sélectionnez le rapport à exporter",
            font=('Arial', 12, 'bold')
        ).pack(pady=10)
        
        tk.Button(
            menu_window,
            text="Rapport complet du parc",
            command=lambda: [self._export_fleet_pdf(), menu_window.destroy()],
            width=30,
            pady=5
        ).pack(pady=5)
        
        tk.Button(
            menu_window,
            text="Annuler",
            command=menu_window.destroy,
            bg='#f44336',
            fg='white'
        ).pack(pady=20)

    def _export_fleet_pdf(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"rapport_parc_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        if filename:
            summary = get_fleet_summary()
            costs = get_detailed_costs_by_vehicle()
            utilization = get_vehicle_utilization_rate()
            
            success, msg = export_fleet_summary_to_pdf(summary, costs, utilization, filename)
            if success:
                messagebox.showinfo("Succès", msg)
            else:
                messagebox.showerror("Erreur", msg)