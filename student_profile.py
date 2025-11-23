"""
Gestion des profils étudiants et de la collecte d'informations
"""
import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from enum import Enum


class InscriptionType(Enum):
    """Types d'inscription"""
    PREMIERE = "premiere_inscription"
    REINSCRIPTION = "reinscription"
    PREP = "prep"
    LAP = "lap"
    MASTER = "master"
    CONCOURS = "concours"


class StudentProfile:
    """Profil d'un étudiant avec toutes ses informations"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        
        # Phase 1 : Informations collectées
        self.phase = "collecte_info"  # ou "remplissage_formulaire"
        self.inscription_type: Optional[str] = None  # "premiere_inscription", "lap", "master", "prep_concours"
        self.is_boursier: Optional[bool] = None
        self.is_mineur: Optional[bool] = None
        self.inscrit_autre_etablissement: Optional[bool] = None
        self.has_jdc: Optional[bool] = None
        
        # Documents nécessaires identifiés
        self.required_documents: List[str] = []
        
        # Phase 2 : Données du formulaire
        self.form_data: Dict = {}
        self.form_completed = False
        
        # Progression
        self.current_step = "start"
        self.completed_steps: List[str] = []
    
    def to_dict(self) -> Dict:
        """Convertit le profil en dictionnaire"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "phase": self.phase,
            "inscription_type": self.inscription_type,
            "is_boursier": self.is_boursier,
            "is_mineur": self.is_mineur,
            "inscrit_autre_etablissement": self.inscrit_autre_etablissement,
            "has_jdc": self.has_jdc,
            "required_documents": self.required_documents,
            "form_data": self.form_data,
            "form_completed": self.form_completed,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "is_phase1_complete": self.is_phase1_complete()  # Inclure le résultat du calcul
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StudentProfile':
        """Crée un profil depuis un dictionnaire"""
        profile = cls(data["session_id"])
        profile.created_at = data.get("created_at", profile.created_at)
        profile.updated_at = data.get("updated_at", profile.updated_at)
        profile.phase = data.get("phase", "collecte_info")
        profile.inscription_type = data.get("inscription_type")
        profile.is_boursier = data.get("is_boursier")
        profile.is_mineur = data.get("is_mineur")
        profile.inscrit_autre_etablissement = data.get("inscrit_autre_etablissement")
        profile.has_jdc = data.get("has_jdc")
        profile.required_documents = data.get("required_documents", [])
        profile.form_data = data.get("form_data", {})
        profile.form_completed = data.get("form_completed", False)
        profile.current_step = data.get("current_step", "start")
        profile.completed_steps = data.get("completed_steps", [])
        return profile
    
    def calculate_required_documents(self) -> List[str]:
        """Calcule les documents nécessaires basés sur les informations collectées"""
        documents = []
        
        # Documents communs à tous
        documents.extend([
            "Photo d'identité (35x45mm, JPG) avec nom, prénom et année d'inscription au verso",
            "Photocopie recto-verso pièce d'identité",
            "Attestation responsabilité civile (année universitaire en cours)",
            "Attestation CVEC (acquittement ou exonération)"
        ])
        
        # PREMIÈRE INSCRIPTION
        if self.inscription_type == "premiere_inscription":
            documents.append("Photocopie diplôme ou relevé notes baccalauréat (si obtenu en 2025)")
            documents.append("Formulaire cession droit à l'image")
            # JDC pour première inscription si pas déjà fournie
            if not self.has_jdc:
                documents.append("Attestation JDC ou attestation d'exemption")
        
        # RÉINSCRIPTION
        elif self.inscription_type in ["lap", "master"]:
            # LAP et Master : mêmes documents (sans formulaire cession droit à l'image)
            documents.append("Autorisation d'inscription")
            documents.append("Carte étudiante de l'année précédente")
            if self.is_mineur:
                documents.append("Autorisation parentale")
            # JDC si pas déjà fournie
            if not self.has_jdc:
                documents.append("Attestation JDC ou attestation d'exemption")
        
        elif self.inscription_type == "prep_concours":
            # Prep' Concours : mêmes documents que LAP/Master (pas de différence)
            documents.append("Autorisation d'inscription")
            documents.append("Carte étudiante de l'année précédente")
            if self.is_mineur:
                documents.append("Autorisation parentale")
            # JDC si pas déjà fournie
            if not self.has_jdc:
                documents.append("Attestation JDC ou attestation d'exemption")
        
        # Documents conditionnels (pour tous)
        if self.is_boursier:
            documents.append("Attestation CROUS portant la mention « boursier » pour l'année universitaire en cours")
        
        if self.inscrit_autre_etablissement:
            documents.append("Copie du bulletin de versement des droits universitaires")
        
        self.required_documents = documents
        return documents
    
    def is_phase1_complete(self) -> bool:
        """Vérifie si la phase 1 (collecte d'infos) est complète"""
        return (
            self.inscription_type is not None and
            self.is_boursier is not None and
            self.is_mineur is not None and
            self.inscrit_autre_etablissement is not None and
            self.has_jdc is not None
        )
    
    def move_to_phase2(self):
        """Passe à la phase 2 (remplissage du formulaire)"""
        if self.is_phase1_complete():
            self.phase = "remplissage_formulaire"
            self.current_step = "personal_info"
            return True
        return False


class ProfileManager:
    """Gère les profils étudiants"""
    
    def __init__(self, storage_dir: str = "./student_profiles"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_profile(self, profile: StudentProfile) -> bool:
        """Sauvegarde un profil"""
        try:
            profile.updated_at = datetime.now().isoformat()
            profile_file = self.storage_dir / f"{profile.session_id}.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du profil: {e}")
            return False
    
    def load_profile(self, session_id: str) -> Optional[StudentProfile]:
        """Charge un profil"""
        try:
            profile_file = self.storage_dir / f"{session_id}.json"
            if not profile_file.exists():
                return None
            
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return StudentProfile.from_dict(data)
        except Exception as e:
            print(f"Erreur lors du chargement du profil: {e}")
            return None
    
    def create_profile(self, session_id: str) -> StudentProfile:
        """Crée un nouveau profil"""
        profile = StudentProfile(session_id)
        self.save_profile(profile)
        return profile
    
    def delete_profile(self, session_id: str) -> bool:
        """Supprime un profil"""
        try:
            profile_file = self.storage_dir / f"{session_id}.json"
            if profile_file.exists():
                profile_file.unlink()
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression du profil: {e}")
            return False

