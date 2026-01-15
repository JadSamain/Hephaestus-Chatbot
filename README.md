# **Fini** le scrolling infini : 

## **Popcorn** 🍿

est votre compagnon cinéma **intelligent** qui fusionne **IA** et **recherche en temps réel** pour **dénicher le synopsis**, **la distribution**, et surtout, la **disponnibilité en streaming** de votre film de ce soir !

## Comment Popcorn fonctionne ?

Popcorn est séparé en 2 : 

- Le corps du projet, le frontend, est lui basé sur du React
- Le cerveau du projet est lui conçu par l’usage du language Python, avec un grand nombre de bibliothèques (telles que FastAPI, Pandas, Playwright etc…)

## ✨ Fonctionnalités

- **🕵️ Recherche "Smart" Hybride** : Popcorn ne se contente pas de sa base de données. S'il ne connaît pas un film, il active son agent de scraping (Playwright) pour aller chercher les infos et disponibilités en temps réel sur le web, puis les mémorise pour la prochaine fois.
- **📂 Catalogue Filtrable** : Explorez une bibliothèque visuelle de films populaires et filtrez-les instantanément par plateforme de streaming ou par recherche textuelle.
- **💾 Mémoire Intelligente** : Vos conversations sont sauvegardées automatiquement en local pour que vous puissiez retrouver cette recommandation de la semaine dernière sans effort.
- **⚡ Indicateurs de Statut** : Suivez la réflexion de l'IA étape par étape (Recherche dans les archives → Analyse web → Réponse) grâce à des indicateurs de chargement dynamiques.

---

## 🛠️ Installation & Démarrage

### Prérequis

- **Node.js** (v18+)
- **Python** (v3.10+)
- **Ollama** (installé et en cours d'exécution)

### 1. Configuration de l'IA (Ollama)

Le projet utilise un modèle personnalisé nommé `Hephaestus-v1`. Assurez-vous d'avoir le fichier `Modelfile` à la racine du projet, puis exécutez :

```bash
# Création du modèle personnalisé basé sur le Modelfile
ollama create Hephaestus-v1 -f Modelfile
```

### 2. Backend (API & Agent)

Le backend gère l'API FastAPI et l'agent de scraping (MCP).

```bash
# Accéder au dossier backend
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # (ou venv\Scripts\activate.ps1 sous Windows)

# Installer les dépendances
pip install -r requirements.txt

# Installer les navigateurs pour Playwright (nécessaire pour le scraping)
playwright install
```

> Note : Assurez-vous que le dossier data/ existe à la racine pour stocker le fichier movies_catalog.csv.
> 

### 3. Frontend (React)

L'interface utilisateur communique avec l'API sur le port 8000.

```bash
# Installer les dépendances JS
npm install packages
```

---

## 🚀 Lancement

Lancez ces commandes dans deux terminaux séparés :

**Terminal 1 : Backend**

```bash
# Se placer à la racine du dossier "backend"
# Démarrage du serveur FastAPI sur http://localhost:8000
python -m app.main
```

**Terminal 2 : Frontend**

```bash
# Se placer à la racine du dossier "front"
# Démarrage de l'interface React
npm run dev
```

Ouvrez votre navigateur sur l'URL indiquée (généralement `http://localhost:5173`) pour commencer à explorer le projet Popcorn ! 🍿
