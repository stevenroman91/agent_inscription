# 🎓 Agent d'inscription Sciences Po Aix

Un système intelligent basé sur RAG (Retrieval-Augmented Generation) pour automatiser et simplifier le processus d'inscription administrative à Sciences Po Aix.

## 🎯 Problèmes résolus

- ✅ **Processus manuel/papier** → Automatisation complète
- ✅ **Dossier mal rempli** → Agent intelligent qui guide les étudiants
- ✅ **Codes inconnus** → Accès direct aux codes depuis les annexes
- ✅ **Pièces manquantes** → Validation automatique des documents
- ✅ **Double travail** → Gestion unifiée de tous les documents

## 🚀 Fonctionnalités

1. **Agent conversationnel intelligent** : Guide les étudiants étape par étape
2. **Système RAG** : Accès instantané à tous les documents officiels (dossier, pièces, codes, annexes)
3. **Validation automatique** : Vérifie que tous les documents sont présents et conformes
4. **Interface web moderne** : Interface intuitive et responsive
5. **Recherche sémantique** : Trouve les informations pertinentes même avec des questions mal formulées

## 📋 Prérequis

- Python 3.8+
- Clé API OpenAI (pour GPT-4 et les embeddings)
- Les documents d'inscription dans le répertoire du projet

## 🔧 Installation

1. **Cloner ou télécharger le projet**

2. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

3. **Configurer la clé API OpenAI** :
```bash
# Créer un fichier .env
echo "OPENAI_API_KEY=votre_cle_api_ici" > .env
```

4. **Placer les documents dans le répertoire** :
   - `Dossier-dinscription-administrative-2025-2026 (2).docx`
   - `Pieces-a-fournir-2025-2026.pdf`
   - `Annexes-inscriptions-administratives-2025-2026.pdf`
   - `PHOTO-2025-11-16-10-33-04.jpg` (exemple de photo)

## 🏃 Utilisation

### Démarrer le serveur

```bash
python main.py
```

L'application sera accessible à l'adresse : `http://localhost:8000`

### Utilisation via l'interface web

1. Ouvrez votre navigateur et allez sur `http://localhost:8000`
2. Posez vos questions dans le chat :
   - "Quelles sont les pièces à fournir ?"
   - "Quels sont les codes pour [catégorie] ?"
   - "Comment remplir le champ [nom du champ] ?"
   - "Aide-moi à comprendre cette question du formulaire"

### Utilisation via l'API

#### Chat avec l'agent
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Quelles sont les pièces à fournir ?"}'
```

#### Obtenir les codes
```bash
curl "http://localhost:8000/api/codes?category=formation"
```

#### Vérifier les documents requis
```bash
curl "http://localhost:8000/api/documents"
```

#### Aide pour un champ spécifique
```bash
curl -X POST "http://localhost:8000/api/help-field?field_name=code_formation"
```

## 📁 Structure du projet

```
SPAix/
├── main.py                      # Application FastAPI principale
├── document_extractor.py        # Extraction de contenu (PDF, DOCX)
├── rag_system.py                # Système RAG avec vector store
├── inscription_agent.py         # Agent intelligent conversationnel
├── document_validator.py        # Validation des documents
├── requirements.txt             # Dépendances Python
├── templates/
│   └── index.html              # Interface web
├── chroma_db/                   # Base de données vectorielle (généré)
└── README.md                    # Ce fichier
```

## 🧠 Architecture

### 1. Extraction de documents
- **PDF** : Utilise `pdfplumber` pour extraire le texte
- **DOCX** : Utilise `python-docx` pour extraire le texte et les tableaux
- **Images** : Extraction des métadonnées

### 2. Système RAG
- **Embeddings** : OpenAI `text-embedding-ada-002`
- **Vector Store** : ChromaDB pour le stockage et la recherche
- **LLM** : GPT-4 Turbo pour les réponses

### 3. Agent intelligent
- **Type** : Agent conversationnel avec mémoire
- **Outils** :
  - Consultation des documents
  - Recherche de codes
  - Vérification des pièces
  - Aide pour les champs du formulaire

### 4. Validation
- Vérification de la présence des documents
- Validation des formats (PDF, JPG, etc.)
- Vérification des tailles
- Validation des spécifications (ex: photo 35x45mm)

## 🔍 Exemples d'utilisation

### Question sur les pièces à fournir
**Utilisateur** : "Quelles sont les pièces à fournir ?"

**Agent** : Liste complète avec détails sur chaque pièce, formats acceptés, et notes importantes.

### Question sur les codes
**Utilisateur** : "Quel code utiliser pour une formation en droit ?"

**Agent** : Recherche dans les annexes et fournit le code exact avec sa description.

### Aide pour remplir un champ
**Utilisateur** : "Je ne comprends pas le champ 'Code formation', comment le remplir ?"

**Agent** : Explique la signification du champ, où trouver le code, et comment le formater.

## 🛠️ Personnalisation

### Modifier les documents sources
Placez vos nouveaux documents dans le répertoire du projet. Le système les détectera automatiquement au redémarrage.

### Ajuster les paramètres RAG
Dans `rag_system.py`, vous pouvez modifier :
- `chunk_size` : Taille des morceaux de texte
- `chunk_overlap` : Chevauchement entre les morceaux
- `search_kwargs["k"]` : Nombre de documents à récupérer

### Personnaliser l'agent
Dans `inscription_agent.py`, modifiez le `system_message` pour changer le comportement de l'agent.

## ⚠️ Notes importantes

- **Coûts API** : L'utilisation d'OpenAI API génère des coûts. Surveillez votre utilisation.
- **Données sensibles** : Les documents d'inscription peuvent contenir des informations sensibles. Assurez-vous de sécuriser votre installation.
- **Performance** : Le premier démarrage peut prendre quelques minutes pour indexer les documents.

## 🐛 Dépannage

### Erreur "OPENAI_API_KEY non définie"
Vérifiez que le fichier `.env` existe et contient votre clé API.

### Erreur lors de l'extraction des documents
Assurez-vous que les fichiers PDF et DOCX ne sont pas corrompus.

### L'agent ne trouve pas d'informations
Vérifiez que les documents sont bien dans le répertoire et que l'indexation s'est bien passée (regardez les logs au démarrage).

## 📝 Licence

Ce projet est fourni à titre d'exemple pour Sciences Po Aix.

## 🤝 Contribution

Les améliorations sont les bienvenues ! N'hésitez pas à proposer des fonctionnalités supplémentaires.

---

**Développé pour simplifier le processus d'inscription à Sciences Po Aix** 🎓

