"""
Gestion des comptes utilisateurs avec base de données
"""
from typing import Optional, Dict
from datetime import datetime
import hashlib
from database import db_manager, UserAccountDB, StudentProfileDB
from user_account import UserAccount
from student_profile import StudentProfile


class DBAccountManager:
    """Gestionnaire de comptes utilisant la base de données"""
    
    def create_account(self, email: str, password: str = None) -> UserAccount:
        """Crée un nouveau compte"""
        session = db_manager.get_session()
        try:
            # Vérifier si le compte existe déjà
            existing = session.query(UserAccountDB).filter_by(email=email).first()
            if existing:
                raise ValueError("Un compte avec cet email existe déjà")
            
            password_hash = None
            if password:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            db_account = UserAccountDB(
                email=email,
                password_hash=password_hash or "",
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            session.add(db_account)
            session.commit()
            
            account = UserAccount(email, password_hash)
            account.created_at = db_account.created_at.isoformat()
            account.last_login = db_account.last_login.isoformat() if db_account.last_login else None
            return account
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_account(self, email: str) -> Optional[UserAccount]:
        """Récupère un compte par email"""
        session = db_manager.get_session()
        try:
            db_account = session.query(UserAccountDB).filter_by(email=email).first()
            if not db_account:
                return None
            
            account = UserAccount(db_account.email, db_account.password_hash)
            account.created_at = db_account.created_at.isoformat() if db_account.created_at else datetime.now().isoformat()
            account.last_login = db_account.last_login.isoformat() if db_account.last_login else None
            
            # Charger les profils associés
            db_profiles = session.query(StudentProfileDB).filter_by(account_id=db_account.id).all()
            account.profiles = {}
            for db_profile in db_profiles:
                from db_student_profile import DBProfileManager
                profile_manager = DBProfileManager()
                profile = profile_manager._db_to_profile(db_profile)
                account.profiles[db_profile.session_id] = profile.to_dict()
            
            return account
        finally:
            session.close()
    
    def verify_password(self, email: str, password: str) -> bool:
        """Vérifie un mot de passe"""
        account = self.get_account(email)
        if not account:
            return False
        return account.verify_password(password)
    
    def login(self, email: str, password: str) -> Optional[UserAccount]:
        """Connecte un utilisateur"""
        if not self.verify_password(email, password):
            return None
        
        session = db_manager.get_session()
        try:
            db_account = session.query(UserAccountDB).filter_by(email=email).first()
            if db_account:
                db_account.last_login = datetime.utcnow()
                session.commit()
            
            return self.get_account(email)
        finally:
            session.close()
    
    def save_profile_to_account(self, email: str, profile: 'StudentProfile') -> bool:
        """Sauvegarde un profil dans un compte"""
        session = db_manager.get_session()
        try:
            db_account = session.query(UserAccountDB).filter_by(email=email).first()
            if not db_account:
                return False
            
            # Vérifier si le profil existe déjà
            db_profile = session.query(StudentProfileDB).filter_by(session_id=profile.session_id).first()
            
            if not db_profile:
                # Créer un nouveau profil lié au compte
                db_profile = StudentProfileDB(
                    session_id=profile.session_id,
                    account_id=db_account.id,
                    phase=profile.phase,
                    inscription_type=profile.inscription_type,
                    is_boursier=profile.is_boursier,
                    is_mineur=profile.is_mineur,
                    inscrit_autre_etablissement=profile.inscrit_autre_etablissement,
                    has_jdc=profile.has_jdc,
                    required_documents=profile.required_documents or [],
                    form_data=profile.form_data or {},
                    form_completed=profile.form_completed,
                    current_step=profile.current_step,
                    completed_steps=profile.completed_steps or []
                )
                session.add(db_profile)
            else:
                # Mettre à jour le profil existant et le lier au compte
                db_profile.account_id = db_account.id
                db_profile.phase = profile.phase
                db_profile.inscription_type = profile.inscription_type
                db_profile.is_boursier = profile.is_boursier
                db_profile.is_mineur = profile.is_mineur
                db_profile.inscrit_autre_etablissement = profile.inscrit_autre_etablissement
                db_profile.has_jdc = profile.has_jdc
                db_profile.required_documents = profile.required_documents or []
                db_profile.form_data = profile.form_data or {}
                db_profile.form_completed = profile.form_completed
                db_profile.current_step = profile.current_step
                db_profile.completed_steps = profile.completed_steps or []
                db_profile.updated_at = datetime.utcnow()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Erreur lors de la sauvegarde du profil dans le compte: {e}")
            return False
        finally:
            session.close()

