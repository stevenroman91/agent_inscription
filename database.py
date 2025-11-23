"""
Système de base de données pour l'application d'inscription
Utilise SQLite avec SQLAlchemy ORM
"""
from sqlalchemy import create_engine, Column, String, Boolean, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional, List, Dict
import json

Base = declarative_base()


class UserAccountDB(Base):
    """Table des comptes utilisateurs"""
    __tablename__ = 'user_accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relation avec les profils
    profiles = relationship("StudentProfileDB", back_populates="account", cascade="all, delete-orphan")


class StudentProfileDB(Base):
    """Table des profils étudiants"""
    __tablename__ = 'student_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey('user_accounts.id'), nullable=True, index=True)
    
    # Phase 1 - Informations collectées
    phase = Column(String(50), default='collecte_info', nullable=False)
    inscription_type = Column(String(50), nullable=True)
    is_boursier = Column(Boolean, nullable=True)
    is_mineur = Column(Boolean, nullable=True)
    inscrit_autre_etablissement = Column(Boolean, nullable=True)
    has_jdc = Column(Boolean, nullable=True)
    
    # Documents requis (stockés en JSON)
    required_documents = Column(JSON, default=list)
    
    # Phase 2 - Données du formulaire (stockées en JSON)
    form_data = Column(JSON, default=dict)
    form_completed = Column(Boolean, default=False)
    current_step = Column(String(50), default='start')
    completed_steps = Column(JSON, default=list)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relation avec le compte
    account = relationship("UserAccountDB", back_populates="profiles")


class DatabaseManager:
    """Gestionnaire de base de données"""
    
    def __init__(self, db_path: str = "./spaix.db"):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Retourne une session de base de données"""
        return self.SessionLocal()
    
    def close(self):
        """Ferme la connexion à la base de données"""
        self.engine.dispose()


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()

