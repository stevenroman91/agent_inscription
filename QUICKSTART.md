# 🚀 Guide de démarrage rapide

## Installation en 3 étapes

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Configurer la clé API OpenAI
Créez un fichier `.env` à la racine du projet :
```bash
echo "OPENAI_API_KEY=votre_cle_api_ici" > .env
```

Vous pouvez obtenir une clé API sur : https://platform.openai.com/api-keys

### 3. Lancer l'application

**Option A - Script automatique (recommandé) :**
```bash
./start.sh
```

**Option B - Manuel :**
```bash
python main.py
```

L'application sera accessible sur : **http://localhost:8000**

## 📝 Vérification de la configuration

Avant de lancer, vous pouvez vérifier que tout est bien configuré :
```bash
python setup.py
```

## 🎯 Utilisation

1. Ouvrez votre navigateur sur `http://localhost:8000`
2. Posez vos questions dans le chat :
   - "Quelles sont les pièces à fournir ?"
   - "Quels sont les codes pour [catégorie] ?"
   - "Comment remplir le champ [nom] ?"
3. Utilisez le bouton "Valider mes documents" pour vérifier vos fichiers

## ⚠️ Notes importantes

- **Premier démarrage** : L'indexation des documents peut prendre 1-2 minutes
- **Coûts API** : L'utilisation d'OpenAI génère des coûts (environ $0.01-0.05 par conversation)
- **Documents requis** : Assurez-vous que les fichiers PDF et DOCX sont dans le répertoire

## 🐛 Problèmes courants

**Erreur "OPENAI_API_KEY non définie"**
→ Vérifiez que le fichier `.env` existe et contient votre clé

**Erreur lors de l'extraction**
→ Vérifiez que les fichiers PDF/DOCX ne sont pas corrompus

**L'agent ne répond pas**
→ Vérifiez votre connexion internet et votre clé API

## 📞 Besoin d'aide ?

Consultez le `README.md` complet pour plus de détails.

