# Déploiement sur Railway

Ce guide explique comment déployer l'application sur Railway.

## Prérequis

1. Un compte Railway (https://railway.app)
2. Une clé API OpenAI
3. Un compte GitHub (optionnel, pour le déploiement automatique)

## Étapes de déploiement

### 1. Préparer le dépôt Git

Assurez-vous que votre code est dans un dépôt Git :

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <votre-repo-url>
git push -u origin main
```

### 2. Créer un projet sur Railway

1. Allez sur https://railway.app
2. Cliquez sur "New Project"
3. Sélectionnez "Deploy from GitHub repo" (ou "Empty Project" si vous préférez déployer manuellement)

### 3. Configurer les variables d'environnement

Dans les paramètres du projet Railway, ajoutez les variables d'environnement suivantes :

- `OPENAI_API_KEY` : Votre clé API OpenAI (obligatoire)

Railway définit automatiquement la variable `PORT`, vous n'avez pas besoin de la configurer.

### 4. Configuration de la base de données

L'application utilise SQLite qui fonctionne bien sur Railway. Les fichiers de base de données seront stockés dans le système de fichiers éphémère de Railway.

⚠️ **Important** : Les données seront perdues lors d'un redéploiement ou d'un redémarrage. Pour une persistance permanente, considérez :
- Utiliser un service de base de données externe (PostgreSQL, MySQL)
- Configurer un volume persistant Railway (si disponible)

### 5. Configuration de ChromaDB

ChromaDB stocke les embeddings des documents dans `./chroma_db/`. Ces données seront également perdues lors d'un redéploiement.

Pour réinitialiser ChromaDB après le déploiement, l'application recréera automatiquement les embeddings au premier démarrage.

### 6. Déploiement

Railway détectera automatiquement :
- Le `Procfile` pour savoir comment démarrer l'application
- Le `requirements.txt` pour installer les dépendances Python
- Le `runtime.txt` pour la version de Python

L'application sera accessible via l'URL fournie par Railway.

## Structure des fichiers de déploiement

- `Procfile` : Commande de démarrage pour Railway
- `runtime.txt` : Version de Python (3.12)
- `requirements.txt` : Dépendances Python
- `railway.json` : Configuration Railway (optionnel)

## Vérification du déploiement

Après le déploiement, vérifiez que :
1. L'application démarre sans erreur
2. Les endpoints API répondent correctement
3. La base de données SQLite est créée
4. ChromaDB initialise correctement les embeddings

## Notes importantes

- **Port** : Railway définit automatiquement la variable `PORT`, le code utilise cette variable
- **Base de données** : SQLite fonctionne mais les données sont éphémères (perdues lors d'un redéploiement)
- **ChromaDB** : Les embeddings seront recréés au premier démarrage (peut prendre quelques minutes)
- **Documents** : Les fichiers PDF/DOCX doivent être présents dans le dépôt Git :
  - `Dossier-dinscription-administrative-2025-2026 (2).docx`
  - `Pieces-a-fournir-2025-2026.pdf`
  - `Annexes-inscriptions-administratives-2025-2026.pdf`
- **Premier démarrage** : Le premier démarrage peut prendre 2-5 minutes car l'application doit :
  1. Extraire le contenu des documents PDF/DOCX
  2. Créer les embeddings avec OpenAI
  3. Initialiser ChromaDB

## Support

En cas de problème, vérifiez les logs Railway dans l'onglet "Deployments" de votre projet.

