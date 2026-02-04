# 🚗 Application de Gestion de Parc Automobile d’Entreprise

## 📌 Présentation

Cette application desktop permet de gérer le **parc automobile d’une entreprise** :
véhicules, employés, réservations, maintenance, carburant, documents et statistiques.

Elle a été développée en **Python** avec :

* **Tkinter** pour l’interface graphique
* **SQLite** pour la base de données
* une architecture **modulaire (UI / services / database)**

Le projet respecte les fonctionnalités demandées dans le sujet.

---

## 🗂️ Fonctionnalités principales

### 🔐 Authentification

* Connexion par **nom d’utilisateur / mot de passe**
* Gestion des rôles :

  * **Admin**
  * **Employé**
* Accès aux écrans selon le rôle

---

### 🚗 Gestion des véhicules

* Ajout / modification de véhicules
* Types de véhicules (voiture, utilitaire, etc.)
* Types d’affectation :

  * `mutualise` (véhicule partagé)
  * `fonction` (véhicule affecté à un employé)
* Statut :

  * disponible
  * en sortie
  * en maintenance

---

### 👤 Gestion des employés

* Ajout et consultation des employés
* Indication de l’autorisation de conduite

---

### 📅 Réservations / sorties

* Réservation de véhicules mutualisés
* Retour de véhicule
* Historique des sorties

---

### 🛠 Maintenance & carburant

* Enregistrement des opérations de maintenance
* Suivi des coûts
* Enregistrement des pleins de carburant
* Historique global

---

### 📄 Gestion des documents

* Documents liés :

  * aux véhicules (assurance, contrôle technique…)
  * aux employés (permis…)
* Suivi des dates d’expiration
* Alerte sur documents proches de l’expiration

---

### 📊 Statistiques / rapports

* Répartition des véhicules par type
* Coûts de maintenance par véhicule
* Vue synthétique du parc

---

## ▶️ Lancer l’application

### 1️⃣ Prérequis

* Python **3.10+**

---

### 2️⃣ Lancer en mode démonstration (recommandé)

Ce mode :

* réinitialise la base de données
* injecte des données cohérentes
* lance l’application automatiquement

```bash
py demo.py
```

#### Comptes de démonstration

| Rôle    | Login    | Mot de passe |
| ------- | -------- | ------------ |
| Admin   | admin    | admin123        |
| Employé | employee | employe123     |

---

### 3️⃣ Lancer normalement

```bash
py main.py
```

⚠️ La base doit déjà exister (ou être créée via `demo.py`).

---

## 🧪 Tests unitaires

Des tests unitaires sont fournis pour la **logique métier** (services).

Lancer tous les tests :

```bash
python -m unittest discover tests
```

---

## 🧠 Choix techniques

* **Séparation claire des responsabilités**

  * UI : affichage et interaction utilisateur
  * Services : règles métier
  * Database : accès aux données
* **SQLite** pour simplicité et portabilité
* **Tkinter** pour une application desktop légère
* Architecture extensible et testable