Membre 1 : Frontend Architect (Interface & UX)

Responsabilité : Développer l'interface utilisateur et la fenêtre de chat.

    Stack Technique : TypeScript avec React, Angular, Vue.js ou Svelte.

Tâches Prioritaires :

    Créer le site vitrine correspondant au thème choisi.

Implémenter le composant de chat (design des bulles, états de chargement).

Gérer la communication asynchrone avec le backend (API REST ou WebSockets).

        Afficher les données structurées renvoyées par le bot (tableaux, listes) et non juste du texte brut.

Membre 2 : Backend Lead (Orchestration & Ollama)

Responsabilité : Cœur du système, gestion des requêtes et connexion à l'IA.

    Stack Technique : Python (FastAPI ou Flask obligatoire).

Tâches Prioritaires :

    Mettre en place le serveur API.

    Connecter le backend à l'instance locale Ollama.

Gérer l'historique de conversation (Contexte) : L'IA doit se souvenir des échanges précédents.

        Définir les endpoints pour recevoir les requêtes du Frontend.

Membre 3 : Tooling Specialist (MCP & Scraping)

Responsabilité : Création des "outils" que l'IA va utiliser.

    Stack Technique : Python, Selenium ou Zendriver.

Tâches Prioritaires :

    Identifier les sources de données externes (sites web) pertinentes pour le thème.

    Développer les scripts de scraping pour extraire les données en temps réel (Interdiction formelle de mock data).

Attention Critique : Ne scraper que des données publiques, sans authentification/paywall.

Structurer les fonctions Python pour qu'elles soient appelables par le "Protocol Tools/MCP".

Membre 4 : Integration & Documentation Lead

Responsabilité : Architecture globale, fusion des composants et livrables écrits.

    Tâches Prioritaires :

        Architecture MCP : Définir le format JSON exact que l'IA doit générer pour déclencher un outil (le "Protocol Tools").

Documentation (Critique) : Rédiger dès maintenant le plan de la documentation technique (7 sections obligatoires) .

Tests d'intégration : Vérifier que quand le Frontend demande une info complexe, le Backend déclenche bien l'outil de scrapping du Membre 3 via la décision de l'IA.

Préparer la présentation de soutenance (20 min).