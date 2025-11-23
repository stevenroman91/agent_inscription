# Base de données SQLite

L'application utilise maintenant **SQLite** avec **SQLAlchemy ORM** pour stocker toutes les données au lieu de fichiers JSON.

## Avantages de la base de données

✅ **Performance** : Requêtes rapides avec index sur les champs fréquemment utilisés  
✅ **Intégrité** : Contraintes de clés étrangères et validation des données  
✅ **Scalabilité** : Facile à migrer vers PostgreSQL/MySQL pour la production  
✅ **Requêtes** : Possibilité de faire des requêtes complexes (recherche, filtres, etc.)  
✅ **Transactions** : Garantie de cohérence des données  
✅ **Relations** : Relations claires entre comptes et profils  

## Structure de la base de données

### Table `user_accounts`
- `id` : Identifiant unique
- `email` : Email (unique, indexé)
- `password_hash` : Hash du mot de passe
- `created_at` : Date de création
- `last_login` : Dernière connexion

### Table `student_profiles`
- `id` : Identifiant unique
- `session_id` : ID de session (unique, indexé)
- `account_id` : Référence au compte (clé étrangère, nullable)
- `phase` : Phase actuelle (collecte_info / remplissage_formulaire)
- `inscription_type` : Type d'inscription
- `is_boursier`, `is_mineur`, etc. : Informations collectées
- `required_documents` : Liste des documents (JSON)
- `form_data` : Données du formulaire (JSON)
- `created_at`, `updated_at` : Métadonnées

## Migration depuis JSON

Pour migrer vos données existantes :

```bash
python migrate_to_db.py
```

Ce script :
1. Lit tous les fichiers JSON dans `student_profiles/` et `user_accounts/`
2. Les importe dans la base de données SQLite (`spaix.db`)
3. Préserve les fichiers JSON originaux

## Utilisation

### Option 1 : Utiliser la BDD (recommandé)

Dans `main.py`, remplacez :
```python
from student_profile import ProfileManager
from user_account import AccountManager

profile_manager = ProfileManager()
account_manager = AccountManager()
```

Par :
```python
from db_student_profile import DBProfileManager
from db_user_account import DBAccountManager

profile_manager = DBProfileManager()
account_manager = DBAccountManager()
```

### Option 2 : Garder les fichiers JSON

Vous pouvez continuer à utiliser les fichiers JSON si vous préférez. Les deux systèmes peuvent coexister.

## Fichier de base de données

La base de données est stockée dans `spaix.db` à la racine du projet.

Pour la production, vous pouvez facilement migrer vers PostgreSQL en changeant la connexion dans `database.py` :

```python
# SQLite (développement)
engine = create_engine('sqlite:///spaix.db')

# PostgreSQL (production)
engine = create_engine('postgresql://user:password@localhost/spaix')
```

## Backup

Pour sauvegarder la base de données :
```bash
cp spaix.db spaix.db.backup
```

Pour restaurer :
```bash
cp spaix.db.backup spaix.db
```

