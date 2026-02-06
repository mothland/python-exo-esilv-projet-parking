from database import get_connection
from datetime import datetime, timedelta


def get_fleet_summary(db_path="db/parc_auto.db"):
    """
    Return fleet summary counts.
    Contract intentionally stable.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM vehicules")
        total = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM vehicules WHERE statut = 'disponible'"
        )
        available = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM vehicules WHERE statut = 'en_sortie'"
        )
        en_sortie = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM vehicules WHERE statut = 'en_maintenance'"
        )
        maintenance = cur.fetchone()[0]

        # Optional extra states (DO NOT expose as official keys)
        cur.execute(
            "SELECT COUNT(*) FROM vehicules WHERE statut = 'en_panne'"
        )
        panne = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM vehicules WHERE statut = 'immobilise'"
        )
        immobilise = cur.fetchone()[0]

    return {
        "total": total,
        "available": available,
        "en_sortie": en_sortie,
        "maintenance": maintenance,

        # extra keys (non-breaking, optional consumers)
        "_panne": panne,
        "_immobilise": immobilise,

        "parc_complet": available == 0 and total > 0,
    }


def get_available_vehicles(db_path="db/parc_auto.db"):
    """
    Return list of available vehicles.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, immatriculation, marque, modele
            FROM vehicules
            WHERE statut = 'disponible'
            ORDER BY marque, modele
            """
        )
        return cur.fetchall()


def get_vehicle_type_counts(db_path="db/parc_auto.db"):
    """
    Return number of vehicles per type.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT type_vehicule, COUNT(*) AS count
            FROM vehicules
            GROUP BY type_vehicule
            """
        )
        rows = cur.fetchall()

    return {row["type_vehicule"]: row["count"] for row in rows}


def get_maintenance_costs_by_vehicle(db_path="db/parc_auto.db"):
    """
    Return total maintenance cost per vehicle.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                v.immatriculation,
                SUM(m.cout) AS total_cout
            FROM maintenances m
            JOIN vehicules v ON v.id = m.vehicule_id
            GROUP BY v.immatriculation
            HAVING total_cout IS NOT NULL
            ORDER BY total_cout DESC
            """
        )
        return cur.fetchall()


# ============================================================================
# NOUVELLES FONCTIONS STATISTIQUES AVANCÉES
# ============================================================================

def get_total_mileage(db_path="db/parc_auto.db"):
    """
    Retourne le kilométrage total de tous les véhicules.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(kilometrage_actuel), 0) as total
            FROM vehicules
        """)
        return cur.fetchone()["total"]


def get_mileage_by_vehicle(db_path="db/parc_auto.db"):
    """
    Retourne le kilométrage par véhicule.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                id,
                immatriculation,
                marque,
                modele,
                kilometrage_actuel as kilometrage,
                type_vehicule
            FROM vehicules
            ORDER BY kilometrage_actuel DESC
        """)
        return cur.fetchall()


def get_mileage_by_period(start_date=None, end_date=None, db_path="db/parc_auto.db"):
    """
    Retourne le kilométrage parcouru par période (basé sur les sorties).
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        
        query = """
            SELECT 
                v.immatriculation,
                v.marque,
                v.modele,
                COALESCE(SUM(s.km_retour - s.km_depart), 0) as km_periode
            FROM vehicules v
            LEFT JOIN sorties_reservations s ON v.id = s.vehicule_id
            WHERE 1=1
        """
        
        params = []
        if start_date:
            query += " AND s.date_sortie_reelle >= ?"
            params.append(start_date)
        if end_date:
            query += " AND s.date_sortie_reelle <= ?"
            params.append(end_date)
            
        query += """
            GROUP BY v.id, v.immatriculation, v.marque, v.modele
            HAVING km_periode > 0
            ORDER BY km_periode DESC
        """
        
        cur.execute(query, params)
        return cur.fetchall()


def get_detailed_costs_by_vehicle(db_path="db/parc_auto.db"):
    """
    Retourne les coûts détaillés par véhicule : carburant, maintenance, assurances, total.
    Inclut les ravitaillements dans les coûts carburant.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                v.id,
                v.immatriculation,
                v.marque,
                v.modele,
                -- Coût carburant = maintenances type carburant + ravitaillements
                COALESCE(SUM(CASE WHEN m.type_intervention LIKE '%carburant%' 
                    OR m.type_intervention LIKE '%essence%'
                    OR m.type_intervention LIKE '%diesel%'
                    OR m.type_intervention LIKE '%ravitaillement%'
                    THEN m.cout ELSE 0 END), 0) + 
                COALESCE((SELECT SUM(r.cout) FROM ravitaillements r WHERE r.vehicule_id = v.id), 0) as cout_carburant,
                -- Coût maintenance = tout sauf carburant et assurance
                COALESCE(SUM(CASE WHEN m.type_intervention NOT LIKE '%carburant%' 
                    AND m.type_intervention NOT LIKE '%essence%'
                    AND m.type_intervention NOT LIKE '%diesel%'
                    AND m.type_intervention NOT LIKE '%ravitaillement%'
                    AND m.type_intervention NOT LIKE '%assurance%'
                    THEN m.cout ELSE 0 END), 0) as cout_maintenance,
                -- Coût assurance
                COALESCE(SUM(CASE WHEN m.type_intervention LIKE '%assurance%' 
                    THEN m.cout ELSE 0 END), 0) as cout_assurance,
                -- Coût total = maintenance + ravitaillements
                COALESCE(SUM(m.cout), 0) + 
                COALESCE((SELECT SUM(r.cout) FROM ravitaillements r WHERE r.vehicule_id = v.id), 0) as cout_total
            FROM vehicules v
            LEFT JOIN maintenances m ON v.id = m.vehicule_id
            GROUP BY v.id, v.immatriculation, v.marque, v.modele
            ORDER BY cout_total DESC
        """)
        return cur.fetchall()


def get_vehicle_utilization_rate(db_path="db/parc_auto.db"):
    """
    Retourne le taux d'occupation et d'utilisation des véhicules.
    Basé sur le nombre de jours d'utilisation sur les 30 derniers jours.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        
        # Date il y a 30 jours
        date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        cur.execute("""
            SELECT 
                v.id,
                v.immatriculation,
                v.marque,
                v.modele,
                v.statut,
                COUNT(DISTINCT DATE(s.date_sortie_reelle)) as jours_utilises,
                COUNT(s.id) as nombre_sorties,
                COALESCE(SUM(s.km_retour - s.km_depart), 0) as km_parcourus,
                ROUND(COUNT(DISTINCT DATE(s.date_sortie_reelle)) * 100.0 / 30, 1) as taux_utilisation
            FROM vehicules v
            LEFT JOIN sorties_reservations s ON v.id = s.vehicule_id 
                AND s.date_sortie_reelle >= ?
                AND s.statut = 'terminee'
            GROUP BY v.id, v.immatriculation, v.marque, v.modele, v.statut
            ORDER BY taux_utilisation DESC
        """, [date_30_days_ago])
        
        return cur.fetchall()


def get_most_active_employees(db_path="db/parc_auto.db"):
    """
    Retourne les employés les plus actifs (nombre de sorties, km parcourus).
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                e.id,
                e.nom,
                e.prenom,
                e.service,
                COUNT(s.id) as nombre_sorties,
                COALESCE(SUM(s.km_retour - s.km_depart), 0) as km_total,
                ROUND(AVG(s.km_retour - s.km_depart), 1) as km_moyen_par_sortie
            FROM employes e
            LEFT JOIN sorties_reservations s ON e.id = s.employe_id
                AND s.statut = 'terminee'
            GROUP BY e.id, e.nom, e.prenom, e.service
            HAVING nombre_sorties > 0
            ORDER BY nombre_sorties DESC
        """)
        return cur.fetchall()


def get_average_consumption_by_vehicle(db_path="db/parc_auto.db"):
    """
    Retourne la consommation moyenne par véhicule.
    Basé sur les coûts de carburant et le kilométrage.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                v.id,
                v.immatriculation,
                v.marque,
                v.modele,
                v.type_vehicule,
                v.kilometrage_actuel as kilometrage,
                COALESCE(SUM(s.km_retour - s.km_depart), 0) as km_parcourus,
                COALESCE(SUM(CASE WHEN m.type_intervention LIKE '%carburant%' 
                    OR m.type_intervention LIKE '%essence%'
                    OR m.type_intervention LIKE '%diesel%'
                    OR m.type_intervention LIKE '%ravitaillement%'
                    THEN m.cout ELSE 0 END), 0) as cout_carburant_total
            FROM vehicules v
            LEFT JOIN sorties_reservations s ON v.id = s.vehicule_id
            LEFT JOIN maintenances m ON v.id = m.vehicule_id
            GROUP BY v.id, v.immatriculation, v.marque, v.modele, v.type_vehicule, v.kilometrage_actuel
            ORDER BY v.immatriculation
        """)
        return cur.fetchall()


def get_average_consumption_by_type(db_path="db/parc_auto.db"):
    """
    Retourne la consommation moyenne par type de véhicule.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                v.type_vehicule,
                COUNT(DISTINCT v.id) as nombre_vehicules,
                COALESCE(SUM(s.km_retour - s.km_depart), 0) as km_total,
                COALESCE(SUM(CASE WHEN m.type_intervention LIKE '%carburant%' 
                    OR m.type_intervention LIKE '%essence%'
                    OR m.type_intervention LIKE '%diesel%'
                    OR m.type_intervention LIKE '%ravitaillement%'
                    THEN m.cout ELSE 0 END), 0) as cout_carburant_total,
                ROUND(AVG(v.kilometrage_actuel), 0) as km_moyen_vehicule
            FROM vehicules v
            LEFT JOIN sorties_reservations s ON v.id = s.vehicule_id
            LEFT JOIN maintenances m ON v.id = m.vehicule_id
            GROUP BY v.type_vehicule
            ORDER BY v.type_vehicule
        """)
        return cur.fetchall()


def get_cost_evolution(months=12, db_path="db/parc_auto.db"):
    """
    Retourne l'évolution des coûts sur les N derniers mois.
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        
        # Date de début
        start_date = (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d')
        
        cur.execute("""
            SELECT 
                strftime('%Y-%m', m.date) as periode,
                COALESCE(SUM(CASE WHEN m.type_intervention LIKE '%carburant%' 
                    OR m.type_intervention LIKE '%essence%'
                    OR m.type_intervention LIKE '%diesel%'
                    OR m.type_intervention LIKE '%ravitaillement%'
                    THEN m.cout ELSE 0 END), 0) as cout_carburant,
                COALESCE(SUM(CASE WHEN m.type_intervention NOT LIKE '%carburant%' 
                    AND m.type_intervention NOT LIKE '%essence%'
                    AND m.type_intervention NOT LIKE '%diesel%'
                    AND m.type_intervention NOT LIKE '%ravitaillement%'
                    THEN m.cout ELSE 0 END), 0) as cout_maintenance,
                COALESCE(SUM(m.cout), 0) as cout_total
            FROM maintenances m
            WHERE m.date >= ?
            GROUP BY periode
            ORDER BY periode
        """, [start_date])
        
        return cur.fetchall()


def export_to_csv(data, headers, filename):
    """
    Exporte des données en CSV.
    
    Args:
        data: Liste de dictionnaires ou de tuples
        headers: Liste des en-têtes de colonnes
        filename: Nom du fichier de sortie
    
    Returns:
        tuple: (success: bool, message: str)
    """
    import csv
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(headers)
            
            for row in data:
                if isinstance(row, dict):
                    writer.writerow([row.get(h, '') for h in headers])
                else:
                    writer.writerow(row)
        
        return True, f"Export CSV réussi : {filename}"
    except Exception as e:
        return False, f"Erreur lors de l'export CSV : {str(e)}"


def export_fleet_summary_to_pdf(summary_data, costs_data, utilization_data, filename):
    """
    Exporte un rapport complet du parc en PDF.
    
    Args:
        summary_data: Dictionnaire avec résumé du parc
        costs_data: Liste des coûts détaillés par véhicule
        utilization_data: Liste des taux d'utilisation
        filename: Nom du fichier de sortie
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Style personnalisé pour le titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1976D2'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Titre
        title = Paragraph("Rapport du Parc Automobile", title_style)
        elements.append(title)
        
        # Date du rapport
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        date_text = Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_style
        )
        elements.append(date_text)
        elements.append(Spacer(1, 20))
        
        # Section 1 : Résumé du parc
        section_title = Paragraph("1. Résumé du parc", styles['Heading2'])
        elements.append(section_title)
        elements.append(Spacer(1, 10))
        
        summary_table_data = [
            ['Indicateur', 'Valeur'],
            ['Total de véhicules', str(summary_data.get('total', 0))],
            ['Disponibles', str(summary_data.get('available', 0))],
            ['En sortie', str(summary_data.get('en_sortie', 0))],
            ['En maintenance', str(summary_data.get('maintenance', 0))],
        ]
        
        summary_table = Table(summary_table_data, colWidths=[10*cm, 5*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Section 2 : Coûts par véhicule
        if costs_data:
            section_title = Paragraph("2. Coûts détaillés par véhicule", styles['Heading2'])
            elements.append(section_title)
            elements.append(Spacer(1, 10))
            
            costs_table_data = [
                ['Immatriculation', 'Carburant', 'Maintenance', 'Assurance', 'Total']
            ]
            
            for row in costs_data[:10]:  # Limite à 10 véhicules
                costs_table_data.append([
                    row['immatriculation'],
                    f"{row['cout_carburant']:.2f} €",
                    f"{row['cout_maintenance']:.2f} €",
                    f"{row['cout_assurance']:.2f} €",
                    f"{row['cout_total']:.2f} €"
                ])
            
            costs_table = Table(costs_table_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3*cm])
            costs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elements.append(costs_table)
            elements.append(Spacer(1, 20))
        
        # Section 3 : Taux d'utilisation
        if utilization_data:
            section_title = Paragraph("3. Taux d'utilisation (30 derniers jours)", styles['Heading2'])
            elements.append(section_title)
            elements.append(Spacer(1, 10))
            
            util_table_data = [
                ['Véhicule', 'Sorties', 'Jours utilisés', 'Km parcourus', 'Taux (%)']
            ]
            
            for row in utilization_data[:10]:
                util_table_data.append([
                    row['immatriculation'],
                    str(row['nombre_sorties']),
                    str(row['jours_utilises']),
                    f"{row['km_parcourus']} km",
                    f"{row['taux_utilisation']}%"
                ])
            
            util_table = Table(util_table_data, colWidths=[4*cm, 2.5*cm, 3*cm, 3*cm, 2.5*cm])
            util_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elements.append(util_table)
        
        # Générer le PDF
        doc.build(elements)
        
        return True, f"Export PDF réussi : {filename}"
    except Exception as e:
        return False, f"Erreur lors de l'export PDF : {str(e)}"