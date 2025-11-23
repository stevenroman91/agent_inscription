"""
Script de migration des données JSON vers la base de données SQLite
"""
import json
from pathlib import Path
from datetime import datetime
from database import db_manager, UserAccountDB, StudentProfileDB
from db_student_profile import DBProfileManager
from db_user_account import DBAccountManager
from student_profile import StudentProfile
from user_account import UserAccount


def migrate_profiles():
    """Migre les profils étudiants depuis les fichiers JSON"""
    print("📦 Migration des profils étudiants...")
    profiles_dir = Path("./student_profiles")
    profile_manager = DBProfileManager()
    
    if not profiles_dir.exists():
        print("   Aucun dossier student_profiles trouvé")
        return
    
    count = 0
    for json_file in profiles_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Créer un profil depuis les données JSON
            profile = StudentProfile.from_dict(data)
            
            # Sauvegarder dans la BDD
            if profile_manager.save_profile(profile):
                count += 1
                print(f"   ✅ Migré: {profile.session_id}")
        except Exception as e:
            print(f"   ❌ Erreur avec {json_file.name}: {e}")
    
    print(f"✅ {count} profils migrés")


def migrate_accounts():
    """Migre les comptes utilisateurs depuis les fichiers JSON"""
    print("📦 Migration des comptes utilisateurs...")
    accounts_dir = Path("./user_accounts")
    account_manager = DBAccountManager()
    profile_manager = DBProfileManager()
    
    if not accounts_dir.exists():
        print("   Aucun dossier user_accounts trouvé")
        return
    
    count = 0
    for json_file in accounts_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            email = data.get("email")
            if not email:
                continue
            
            # Vérifier si le compte existe déjà
            existing = account_manager.get_account(email)
            if existing:
                print(f"   ⏭️  Compte {email} existe déjà, mise à jour...")
                db_account = None
                session = db_manager.get_session()
                try:
                    db_account = session.query(UserAccountDB).filter_by(email=email).first()
                finally:
                    session.close()
            else:
                # Créer le compte
                password_hash = data.get("password_hash", "")
                account = UserAccount(email, password_hash)
                account.created_at = data.get("created_at", account.created_at)
                account.last_login = data.get("last_login")
                
                # Créer dans la BDD
                session = db_manager.get_session()
                try:
                    db_account = UserAccountDB(
                        email=email,
                        password_hash=password_hash,
                        created_at=datetime.fromisoformat(account.created_at) if account.created_at else datetime.utcnow(),
                        last_login=datetime.fromisoformat(account.last_login) if account.last_login else None
                    )
                    session.add(db_account)
                    session.commit()
                    session.refresh(db_account)
                finally:
                    session.close()
            
            # Migrer les profils associés
            profiles_data = data.get("profiles", {})
            for session_id, profile_data in profiles_data.items():
                try:
                    profile = StudentProfile.from_dict(profile_data)
                    # Lier le profil au compte
                    session = db_manager.get_session()
                    try:
                        db_profile = session.query(StudentProfileDB).filter_by(session_id=session_id).first()
                        if db_profile:
                            db_profile.account_id = db_account.id
                            session.commit()
                        else:
                            # Créer le profil
                            profile_manager.save_profile(profile)
                            # Le lier au compte
                            db_profile = session.query(StudentProfileDB).filter_by(session_id=session_id).first()
                            if db_profile:
                                db_profile.account_id = db_account.id
                                session.commit()
                    finally:
                        session.close()
                except Exception as e:
                    print(f"   ⚠️  Erreur avec le profil {session_id}: {e}")
            
            count += 1
            print(f"   ✅ Migré: {email}")
        except Exception as e:
            print(f"   ❌ Erreur avec {json_file.name}: {e}")
    
    print(f"✅ {count} comptes migrés")


if __name__ == "__main__":
    print("🚀 Début de la migration vers la base de données...")
    print("=" * 50)
    
    migrate_profiles()
    print()
    migrate_accounts()
    
    print("=" * 50)
    print("✅ Migration terminée !")
    print("💡 Les fichiers JSON originaux sont conservés pour référence")

