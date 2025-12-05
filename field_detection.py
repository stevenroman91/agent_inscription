"""
Détection intelligente des champs du formulaire et de leurs types
Analyse section par section pour comprendre les formats, codes, et structures
"""
from typing import Dict, Optional, List, Tuple
from form_sections import FORM_SECTIONS, get_section_by_field

# Types de champs détectés
FIELD_TYPES = {
    "text": "Texte libre",
    "text_uppercase": "Texte en MAJUSCULES",
    "numeric": "Numérique",
    "numeric_fixed": "Numérique avec longueur fixe",
    "date": "Date (JJ/MM/AAAA)",
    "choice": "Choix parmi options",
    "code_annexe": "Code depuis annexe",
    "address": "Adresse complète",
    "year": "Année",
    "checkbox": "Case à cocher"
}

# Mapping des champs vers leurs types et formats
FIELD_DETECTION = {}

def analyze_all_sections():
    """Analyse toutes les sections pour créer le mapping de détection"""
    global FIELD_DETECTION
    
    for section in FORM_SECTIONS:
        if "field" in section:
            # Section simple avec un seul champ
            field_name = section["field"]
            field_type = section.get("type", "text")
            format_info = section.get("format", "")
            
            FIELD_DETECTION[field_name] = {
                "type": detect_field_type(field_type, format_info, section),
                "format": format_info,
                "options": section.get("options", []),
                "section": section["number"],
                "requires_code": "annexe" in format_info.lower()
            }
        elif "fields" in section:
            # Section avec plusieurs champs
            for field_name, field_info in section["fields"].items():
                field_type = field_info.get("type", "text")
                format_info = field_info.get("format", "")
                
                FIELD_DETECTION[field_name] = {
                    "type": detect_field_type(field_type, format_info, field_info),
                    "format": format_info,
                    "options": field_info.get("options", []),
                    "section": section["number"],
                    "requires_code": "annexe" in format_info.lower(),
                    "annexe_number": extract_annexe_number(format_info) if "annexe" in format_info.lower() else None
                }

def detect_field_type(field_type: str, format_info: str, field_data: Dict) -> str:
    """Détecte le type de champ basé sur le type, format et données"""
    format_lower = format_info.lower()
    
    # Choix multiples
    if field_type == "choice" or "choisir" in format_lower or "options" in field_data:
        return "choice"
    
    # Checkbox
    if field_type == "checkbox":
        return "checkbox"
    
    # Date
    if "jj/mm/aaaa" in format_lower or "date" in format_lower:
        return "date"
    
    # Année
    if "année" in format_lower or "annee" in format_lower:
        return "year"
    
    # Numérique avec longueur fixe
    if "caractères" in format_lower or "chiffres" in format_lower:
        length = extract_number(format_lower)
        if length:
            return f"numeric_{length}"
    
    # Numérique simple
    if "code" in format_lower and "annexe" in format_lower:
        return "code_annexe"
    
    # Adresse
    if "adresse" in format_lower and "complète" in format_lower:
        return "address"
    
    # Texte en majuscules
    if "majuscules" in format_lower or "uppercase" in format_lower:
        return "text_uppercase"
    
    # Texte par défaut
    return "text"

def extract_number(text: str) -> Optional[int]:
    """Extrait un nombre d'un texte"""
    import re
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else None

def extract_annexe_number(format_info: str) -> Optional[int]:
    """Extrait le numéro d'annexe du format"""
    import re
    match = re.search(r'annexe\s*(\d+)', format_info.lower())
    return int(match.group(1)) if match else None

def get_field_info(field_name: str) -> Optional[Dict]:
    """Retourne les informations d'un champ"""
    return FIELD_DETECTION.get(field_name)

def requires_code(field_name: str) -> bool:
    """Vérifie si un champ nécessite un code d'annexe"""
    field_info = get_field_info(field_name)
    return field_info.get("requires_code", False) if field_info else False

def get_annexe_number(field_name: str) -> Optional[int]:
    """Retourne le numéro d'annexe requis pour un champ"""
    field_info = get_field_info(field_name)
    return field_info.get("annexe_number") if field_info else None

def is_choice_field(field_name: str) -> bool:
    """Vérifie si un champ est un choix multiple"""
    field_info = get_field_info(field_name)
    return field_info.get("type") == "choice" if field_info else False

def get_choice_options(field_name: str) -> List[str]:
    """Retourne les options pour un champ de type choice"""
    field_info = get_field_info(field_name)
    return field_info.get("options", []) if field_info else []

# Initialiser le mapping au chargement du module
analyze_all_sections()

