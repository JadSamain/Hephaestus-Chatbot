# 🚀 Guide de Lancement : Hephaestus Chatbot

Ce document détaille la procédure complète pour lancer l'écosystème : **Frontend (React)**, **Backend (FastAPI)** et le **Modèle Local (Ollama)**.

## 1. Prérequis Système

Assurez-vous d'avoir les outils suivants installés sur votre machine :

- **Node.js (v18+)** : Pour exécuter le frontend.
- **Python (3.10+)** : Pour exécuter le backend.
- **Ollama** : Pour gérer et exécuter le modèle d'IA localement.

## 2. Préparation du Modèle (Ollama)

Avant de lancer les serveurs, vous devez enregistrer le modèle personnalisé dans Ollama.

1.  Ouvrez un terminal.
2.  Placez-vous à la racine du projet (là où se trouve le fichier `Modelfile`).
3.  Créez le modèle avec la commande suivante :

```bash
ollama create Hephaestus-v1 -f Modelfile
```

4.  Vérifiez que le modèle a bien été créé :

```bash
ollama list
```

## 3. Lancement du Backend (FastAPI)

Le backend agit comme une passerelle entre l'interface utilisateur et Ollama.

1.  Ouvrez un **nouveau terminal** et naviguez vers le dossier backend :

```bash
cd backend
```

2.  Activez l'environnement virtuel (si ce n'est pas déjà fait) :

```bash
source venv/bin/activate
# Sur Windows : venv\Scripts\activate
```

3.  Lancez le serveur :

```bash
python -m app.main
```

> [!TIP]
> Le serveur est opérationnel lorsque vous voyez le message :  
> `Uvicorn running on http://127.0.0.1:8000`.

## 4. Lancement du Frontend (React + Vite)

L'interface utilisateur vous permet d'interagir avec l'IA.

1.  Ouvrez un **deuxième terminal** et allez dans le dossier frontend :

```bash
cd front
```

2.  Installez les dépendances (uniquement lors de la première utilisation) :

```bash
npm install
```

3.  Lancez l'application en mode développement :

```bash
npm run dev
```

4.  Cliquez sur l'URL affichée (par défaut `http://localhost:5173`) pour ouvrir le chat dans votre navigateur.

## 5. Procédure de Test

Pour valider le bon fonctionnement de l'application, effectuez les vérifications suivantes :

- [ ] **Vérification visuelle** : L'en-tête de la page affiche "POPCORN Chat".
- [ ] **Envoi d'un message** : Tapez "Bonjour Hephaestus" et envoyez le message.
- [ ] **Analyse des logs** :
    - **Backend** : Vous devriez voir `[*] Envoi du prompt à Ollama...`.
    - **Navigateur** : Une réponse générée par l'IA doit s'afficher.
- [ ] **Test de spécialisation** : Demandez une recommandation de film (ex: "Conseille-moi un film de science-fiction") pour vérifier que le contexte du `Modelfile` est bien pris en compte.

## 🛠 Dépannage Rapide

| Problème | Solution Possible |
| :--- | :--- |
| **Erreur de connexion (Frontend)** | Vérifiez que le backend tourne bien sur le port `8000`. |
| **ModuleNotFoundError** | Lancez bien le backend avec `python -m app.main` depuis le dossier `backend/`, et non depuis `backend/app/`. |
| **Réponse vide** | Assurez-vous qu'Ollama tourne en arrière-plan (`ollama serve`). |