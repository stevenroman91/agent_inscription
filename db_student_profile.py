"""
Gestion des profils étudiants avec base de données
"""
from typing import Optional, List, Dict
from datetime import datetime
from database import db_manager, StudentProfileDB, UserAccountDB
from student_profile import StudentProfile


class DBProfileManager:
    """Gestionnaire de profils utilisant la base de données"""
    
    def create_profile(self, session_id: str, account_id: Optional[int] = None) -> StudentProfile:
        """Crée un nouveau profil étudiant"""
        session = db_manager.get_session()
        try:
            # Vérifier si le profil existe déjà
            existing = session.query(StudentProfileDB).filter_by(session_id=session_id).first()
            if existing:
                return self._db_to_profile(existing)
            
            # Créer un nouveau profil
            db_profile = StudentProfileDB(
                session_id=session_id,
                account_id=account_id,
                phase='collecte_info',
                required_documents=[],
                form_data={},
                completed_steps=[]
            )
            session.add(db_profile)
            session.commit()
            return self._db_to_profile(db_profile)
        finally:
            session.close()
    
    def load_profile(self, session_id: str) -> Optional[StudentProfile]:
        """Charge un profil étudiant"""
        session = db_manager.get_session()
        try:
            db_profile = session.query(StudentProfileDB).filter_by(session_id=session_id).first()
            if not db_profile:
                return None
            return self._db_to_profile(db_profile)
        finally:
            session.close()
    
    def save_profile(self, profile: StudentProfile) -> bool:
        """Sauvegarde un profil étudiant"""
        session = db_manager.get_session()
        try:
            db_profile = session.query(StudentProfileDB).filter_by(session_id=profile.session_id).first()
            
            if not db_profile:
                # Créer un nouveau profil
                db_profile = StudentProfileDB(session_id=profile.session_id)
                session.add(db_profile)
            
            # Mettre à jour les champs
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
            print(f"Erreur lors de la sauvegarde du profil: {e}")
            return False
        finally:
            session.close()
    
    def delete_profile(self, session_id: str) -> bool:
        """Supprime un profil étudiant"""
        session = db_manager.get_session()
        try:
            db_profile = session.query(StudentProfileDB).filter_by(session_id=session_id).first()
            if db_profile:
                session.delete(db_profile)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Erreur lors de la suppression du profil: {e}")
            return False
        finally:
            session.close()
    
    def get_profiles_by_account(self, account_id: int) -> List[StudentProfile]:
        """Récupère tous les profils d'un compte"""
        session = db_manager.get_session()
        try:
            db_profiles = session.query(StudentProfileDB).filter_by(account_id=account_id).all()
            return [self._db_to_profile(p) for p in db_profiles]
        finally:
            session.close()
    
    def _db_to_profile(self, db_profile: StudentProfileDB) -> StudentProfile:
        """Convertit un profil DB en StudentProfile"""
        profile = StudentProfile(db_profile.session_id)
        profile.created_at = db_profile.created_at.isoformat() if db_profile.created_at else datetime.now().isoformat()
        profile.updated_at = db_profile.updated_at.isoformat() if db_profile.updated_at else datetime.now().isoformat()
        profile.phase = db_profile.phase
        profile.inscription_type = db_profile.inscription_type
        profile.is_boursier = db_profile.is_boursier
        profile.is_mineur = db_profile.is_mineur
        profile.inscrit_autre_etablissement = db_profile.inscrit_autre_etablissement
        profile.has_jdc = db_profile.has_jdc
        profile.required_documents = db_profile.required_documents or []
        profile.form_data = db_profile.form_data or {}
        profile.form_completed = db_profile.form_completed
        profile.current_step = db_profile.current_step
        profile.completed_steps = db_profile.completed_steps or []
        return profile

