"""
Système de validation des pièces à fournir
"""
from typing import List, Dict, Optional
from pathlib import Path
from PIL import Image
import os


class DocumentValidator:
    """Valide les documents fournis par les étudiants"""
    
    REQUIRED_DOCUMENTS = [
        {
            "name": "Attestation de participation à la journée Défense et Citoyenneté",
            "required": True,
            "formats": ["pdf", "jpg", "jpeg", "png"],
            "max_size_mb": 5
        },
        {
            "name": "Attestation de responsabilité civile",
            "required": True,
            "formats": ["pdf", "jpg", "jpeg", "png"],
            "max_size_mb": 5,
            "notes": "Doit contenir le nom de l'étudiant, mention extra-scolaire, et couvrir l'année en cours"
        },
        {
            "name": "Attestation CVEC",
            "required": True,
            "formats": ["pdf", "jpg", "jpeg", "png"],
            "max_size_mb": 5,
            "notes": "Doit contenir le numéro CVEC (format: AIX0-XXXXXX-XX)"
        },
        {
            "name": "Formulaire Cession droit à l'image",
            "required": True,
            "formats": ["pdf"],
            "max_size_mb": 5
        },
        {
            "name": "Justificatif d'identité",
            "required": True,
            "formats": ["pdf", "jpg", "jpeg", "png"],
            "max_size_mb": 5,
            "notes": "Carte d'identité, passeport ou autre document officiel en cours de validité"
        },
        {
            "name": "Photocopie des diplômes et relevés de notes",
            "required": True,
            "formats": ["pdf", "jpg", "jpeg", "png"],
            "max_size_mb": 10,
            "notes": "Dernière formation validée en France ou à l'étranger"
        },
        {
            "name": "Photo d'identité",
            "required": True,
            "formats": ["jpg", "jpeg"],
            "max_size_mb": 2,
            "notes": "Format 35x45mm, JPG uniquement (pas de PDF)",
            "image_specs": {
                "width": 35,
                "height": 45,
                "unit": "mm"
            }
        }
    ]
    
    def __init__(self):
        self.validation_results = []
    
    def validate_file(self, file_path: str, document_type: str) -> Dict[str, any]:
        """Valide un fichier selon son type"""
        path = Path(file_path)
        
        if not path.exists():
            return {
                "valid": False,
                "errors": [f"Le fichier {file_path} n'existe pas"]
            }
        
        # Trouver la spécification du document
        doc_spec = next(
            (doc for doc in self.REQUIRED_DOCUMENTS if doc["name"] == document_type),
            None
        )
        
        if not doc_spec:
            return {
                "valid": False,
                "errors": [f"Type de document inconnu: {document_type}"]
            }
        
        errors = []
        warnings = []
        
        # Vérifier l'extension
        file_ext = path.suffix.lower().lstrip('.')
        if file_ext not in doc_spec["formats"]:
            errors.append(
                f"Format invalide: {file_ext}. Formats acceptés: {', '.join(doc_spec['formats'])}"
            )
        
        # Vérifier la taille
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > doc_spec["max_size_mb"]:
            errors.append(
                f"Fichier trop volumineux: {file_size_mb:.2f}MB. Maximum: {doc_spec['max_size_mb']}MB"
            )
        
        # Vérifications spécifiques pour les images
        if file_ext in ["jpg", "jpeg", "png"]:
            try:
                with Image.open(file_path) as img:
                    # Vérifier les dimensions pour la photo d'identité
                    if document_type == "Photo d'identité":
                        # Convertir mm en pixels (approximatif: 300 DPI)
                        expected_width_px = int(doc_spec.get("image_specs", {}).get("width", 0) * 11.81)
                        expected_height_px = int(doc_spec.get("image_specs", {}).get("height", 0) * 11.81)
                        
                        width, height = img.size
                        # Tolérance de 10%
                        if abs(width - expected_width_px) > expected_width_px * 0.1:
                            warnings.append(
                                f"Largeur de l'image ({width}px) peut ne pas correspondre au format requis (35mm)"
                            )
                        if abs(height - expected_height_px) > expected_height_px * 0.1:
                            warnings.append(
                                f"Hauteur de l'image ({height}px) peut ne pas correspondre au format requis (45mm)"
                            )
                    
                    # Vérifier le mode de l'image
                    if img.mode not in ["RGB", "L"]:
                        warnings.append(f"Mode d'image: {img.mode}. RGB recommandé.")
            except Exception as e:
                errors.append(f"Impossible de lire l'image: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "file_path": file_path,
            "file_size_mb": round(file_size_mb, 2),
            "document_type": document_type
        }
    
    def validate_all_documents(self, documents_dir: str) -> Dict[str, any]:
        """Valide tous les documents dans un répertoire"""
        results = {
            "valid": True,
            "documents": [],
            "missing": [],
            "summary": {
                "total_required": len(self.REQUIRED_DOCUMENTS),
                "found": 0,
                "valid": 0,
                "invalid": 0,
                "missing": 0
            }
        }
        
        # Créer un mapping des fichiers trouvés
        found_files = {}
        path = Path(documents_dir)
        
        for file_path in path.glob("*"):
            if file_path.is_file():
                # Essayer de deviner le type de document par le nom du fichier
                file_name_lower = file_path.name.lower()
                for doc in self.REQUIRED_DOCUMENTS:
                    doc_name_lower = doc["name"].lower()
                    # Correspondance simple basée sur des mots-clés
                    keywords = {
                        "Attestation de participation à la journée Défense et Citoyenneté": ["defense", "citoyenneté", "jdc"],
                        "Attestation de responsabilité civile": ["responsabilité", "civile", "assurance"],
                        "Attestation CVEC": ["cvec"],
                        "Formulaire Cession droit à l'image": ["cession", "image", "droit"],
                        "Justificatif d'identité": ["identité", "cni", "passeport", "carte"],
                        "Photocopie des diplômes et relevés de notes": ["diplôme", "relevé", "notes", "bulletin"],
                        "Photo d'identité": ["photo", "identité"]
                    }
                    
                    if any(keyword in file_name_lower for keyword in keywords.get(doc["name"], [])):
                        if doc["name"] not in found_files:
                            found_files[doc["name"]] = str(file_path)
                            break
        
        # Valider les fichiers trouvés
        for doc in self.REQUIRED_DOCUMENTS:
            if doc["name"] in found_files:
                validation = self.validate_file(found_files[doc["name"]], doc["name"])
                results["documents"].append(validation)
                results["summary"]["found"] += 1
                if validation["valid"]:
                    results["summary"]["valid"] += 1
                else:
                    results["summary"]["invalid"] += 1
                    results["valid"] = False
            else:
                if doc["required"]:
                    results["missing"].append(doc["name"])
                    results["summary"]["missing"] += 1
                    results["valid"] = False
        
        return results
    
    def get_validation_report(self, validation_results: Dict[str, any]) -> str:
        """Génère un rapport de validation lisible"""
        report = []
        report.append("=" * 60)
        report.append("RAPPORT DE VALIDATION DES DOCUMENTS")
        report.append("=" * 60)
        report.append("")
        
        summary = validation_results["summary"]
        report.append(f"Documents requis: {summary['total_required']}")
        report.append(f"Documents trouvés: {summary['found']}")
        report.append(f"Documents valides: {summary['valid']}")
        report.append(f"Documents invalides: {summary['invalid']}")
        report.append(f"Documents manquants: {summary['missing']}")
        report.append("")
        
        if validation_results["missing"]:
            report.append("⚠️  DOCUMENTS MANQUANTS:")
            for doc in validation_results["missing"]:
                report.append(f"  - {doc}")
            report.append("")
        
        if validation_results["documents"]:
            report.append("📄 VALIDATION DES DOCUMENTS:")
            for doc_result in validation_results["documents"]:
                status = "✅" if doc_result["valid"] else "❌"
                report.append(f"{status} {doc_result['document_type']}")
                report.append(f"   Fichier: {doc_result['file_path']}")
                report.append(f"   Taille: {doc_result['file_size_mb']}MB")
                
                if doc_result["errors"]:
                    for error in doc_result["errors"]:
                        report.append(f"   ❌ Erreur: {error}")
                
                if doc_result["warnings"]:
                    for warning in doc_result["warnings"]:
                        report.append(f"   ⚠️  Avertissement: {warning}")
                report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)

