"""
Système de sauvegarde de progression pour le formulaire d'inscription
"""
import json
import os
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime


class FormProgressManager:
    """Gère la sauvegarde et le chargement de la progression du formulaire"""
    
    def __init__(self, storage_dir: str = "./form_progress"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_progress(self, session_id: str, form_data: Dict, current_step: str) -> bool:
        """Sauvegarde la progression du formulaire"""
        try:
            progress_file = self.storage_dir / f"{session_id}.json"
            progress_data = {
                "session_id": session_id,
                "form_data": form_data,
                "current_step": current_step,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def load_progress(self, session_id: str) -> Optional[Dict]:
        """Charge la progression du formulaire"""
        try:
            progress_file = self.storage_dir / f"{session_id}.json"
            if not progress_file.exists():
                return None
            
            with open(progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement: {e}")
            return None
    
    def delete_progress(self, session_id: str) -> bool:
        """Supprime la progression sauvegardée"""
        try:
            progress_file = self.storage_dir / f"{session_id}.json"
            if progress_file.exists():
                progress_file.unlink()
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression: {e}")
            return False

