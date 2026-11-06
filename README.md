# VocaNégoce

Application web de gestion commerciale développée avec Django, dédiée au négoce de produits chimiques et équipements. Elle intègre une recherche intelligente, un assistant vocal ElevenLabs, et la génération de factures PDF.

## Fonctionnalités

### Tableau de bord
- Statistiques globales : nombre de produits, clients, commandes
- Alertes de stock faible
- Chiffre d'affaires total (commandes livrées)
- Dernières commandes enregistrées

### Gestion des produits
- CRUD complet (créer, lire, modifier, supprimer)
- Catégories : chimique, équipement, consommable, autre
- Suivi du stock avec seuil minimum d'alerte
- Upload d'images produits
- Support des formules chimiques
- Recherche sémantique avec scoring de pertinence et recherche floue (synonymes, fautes de frappe)

### Gestion des clients
- CRUD complet
- Informations entreprise (raison sociale, SIRET, contact, adresse)
- Statuts : actif, inactif, suspendu
- Historique des commandes par client avec calcul du CA

### Gestion des commandes
- Création de commandes multi-produits
- Calcul automatique des totaux
- Gestion automatique des stocks (décrémentation/restauration)
- Statuts : en attente, confirmée, en préparation, expédiée, livrée, annulée
- Génération automatique du numéro de commande

### Recherche intelligente
- API de recherche unifiée (produits, clients, commandes)
- Auto-complétion en temps réel
- Recherche sémantique avec scoring de pertinence
- Recherche floue avec gestion des synonymes
- Journalisation des recherches (SearchLog)

### Assistant vocal ElevenLabs
- Intégration de l'assistant IA ElevenLabs
- API contextuelle fournissant les données de l'application (stats, activité récente)

### Facturation
- Génération de factures PDF (xhtml2pdf)
- Modèle de facture personnalisable

### Chiffre d'affaires
- CA total (commandes livrées)
- CA mensuel (année en cours)
- CA annuel

### Authentification
- Inscription et connexion utilisateur
- Accès protégé par `@login_required`

## Technologies utilisées

| Technologie | Rôle |
|---|---|
| Django 5.2 | Framework backend |
| SQLite | Base de données |
| Bootstrap 5.3 | Frontend (CDN) |
| Font Awesome 6.4 | Icônes (CDN) |
| xhtml2pdf | Génération de factures PDF |
| Pillow | Gestion des images produits |
| ElevenLabs | Assistant vocal IA |

## Installation

### Prérequis
- Python 3.10+
- pip

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/FADWA673/vocanegoce.git
cd vocanegoce

# 2. Créer un environnement virtuel
python -m venv venv

# 3. Activer l'environnement virtuel
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Appliquer les migrations
python manage.py migrate

# 6. Créer un superutilisateur (pour l'admin Django)
python manage.py createsuperuser

# 7. Lancer le serveur
python manage.py runserver
```

L'application est accessible sur `http://127.0.0.1:8000/`

## Structure du projet

```
vocanegoce_project/
├── manage.py
├── requirements.txt
├── db.sqlite3                  # Base de données (non versionnée)
├── vocanegoce_project/         # Configuration Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── gestion/                    # Application principale
│   ├── models.py               # Modèles : Produit, Client, Commande, DetailCommande, SearchLog
│   ├── views.py                # Vues et logique métier
│   ├── forms.py                # Formulaires (ProduitForm, ClientForm, CommandeForm)
│   ├── urls.py                 # Routes de l'application
│   ├── admin.py
│   ├── templates/
│   │   ├── base.html           # Template de base (Bootstrap, navbar)
│   │   ├── Dashboard.html
│   │   ├── registration/        # Login, register
│   │   └── gestion/             # Templates CRUD, facture, recherche, assistant
│   └── migrations/
├── media/                      # Fichiers uploadés (non versionné)
│   └── produits/               # Images des produits
├── static/                     # Fichiers statiques
└── logs/                       # Logs applicatifs (non versionné)
```

## Modèles de données

- **Produit** : nom, description, catégorie, prix, stock, seuil_minimum, unité, formule_chimique, image, actif
- **Client** : raison_sociale, siret, contact, email, téléphone, adresse, ville, code_postal, statut, notes
- **Commande** : numero_commande (auto), client, date_commande, statut, notes, total
- **DetailCommande** : commande, produit, quantité, prix_unitaire, sous_total (calculé)
- **SearchLog** : utilisateur, terme_recherche, type_recherche, resultats_count, date_creation

## Configuration

Le fichier `settings.py` contient :
- `SECRET_KEY` : à modifier pour la production
- `DEBUG = True` : à passer à `False` en production
- `ALLOWED_HOSTS` : à configurer selon le domaine de production
- Paramètres de sécurité activés automatiquement quand `DEBUG = False`

## Licence

Projet privé - Tous droits réservés.
