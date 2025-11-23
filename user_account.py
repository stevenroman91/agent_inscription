"""
Système de gestion des comptes utilisateurs pour sauvegarder la progression
"""
import json
import os
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import hashlib


class UserAccount:
    """Compte utilisateur avec sauvegarde de progression"""
    
    def __init__(self, email: str, password_hash: str = None):
        self.email = email
        self.password_hash = password_hash
        self.created_at = datetime.now().isoformat()
        self.last_login = datetime.now().isoformat()
        self.profiles: Dict[str, Dict] = {}  # session_id -> profile_data
        self.current_session_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convertit le compte en dictionnaire"""
        return {
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "profiles": self.profiles,
            "current_session_id": self.current_session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserAccount':
        """Crée un compte depuis un dictionnaire"""
        account = cls(data["email"], data.get("password_hash"))
        account.created_at = data.get("created_at", account.created_at)
        account.last_login = data.get("last_login", account.last_login)
        account.profiles = data.get("profiles", {})
        account.current_session_id = data.get("current_session_id")
        return account
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash un mot de passe"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Vérifie un mot de passe"""
        if not self.password_hash:
            return True  # Pas de mot de passe défini
        return self.hash_password(password) == self.password_hash
    
    def save_profile(self, session_id: str, profile_data: Dict):
        """Sauvegarde un profil associé à ce compte"""
        self.profiles[session_id] = profile_data
        self.current_session_id = session_id
        self.last_login = datetime.now().isoformat()


class AccountManager:
    """Gère les comptes utilisateurs"""
    
    def __init__(self, storage_dir: str = "./user_accounts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def create_account(self, email: str, password: str = None) -> UserAccount:
        """Crée un nouveau compte"""
        account_file = self.storage_dir / f"{email.replace('@', '_at_')}.json"
        if account_file.exists():
            raise ValueError("Un compte avec cet email existe déjà")
        
        password_hash = UserAccount.hash_password(password) if password else None
        account = UserAccount(email, password_hash)
        self.save_account(account)
        return account
    
    def get_account(self, email: str) -> Optional[UserAccount]:
        """Récupère un compte"""
        account_file = self.storage_dir / f"{email.replace('@', '_at_')}.json"
        if not account_file.exists():
            return None
        
        try:
            with open(account_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return UserAccount.from_dict(data)
        except Exception as e:
            print(f"Erreur lors du chargement du compte: {e}")
            return None
    
    def save_account(self, account: UserAccount) -> bool:
        """Sauvegarde un compte"""
        try:
            account_file = self.storage_dir / f"{account.email.replace('@', '_at_')}.json"
            with open(account_file, 'w', encoding='utf-8') as f:
                json.dump(account.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du compte: {e}")
            return False
    
    def authenticate(self, email: str, password: str) -> Optional[UserAccount]:
        """Authentifie un utilisateur"""
        account = self.get_account(email)
        if not account:
            return None
        
        if account.verify_password(password):
            account.last_login = datetime.now().isoformat()
            self.save_account(account)
            return account
        return None

