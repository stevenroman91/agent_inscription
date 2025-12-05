"""
Liste complète des sections du formulaire d'inscription (24 cadres)
Basé sur l'analyse du document Dossier-dinscription-administrative-2025-2026
"""
from typing import List, Dict, Optional

FORM_SECTIONS = [
    {
        "number": 1,
        "name": "Inscription A AMU",
        "field": "type_inscription",
        "required": True,
        "type": "choice",
        "options": ["1ère Inscription", "Réinscription"],
        "format": "Choisir entre '1ère Inscription' ou 'Réinscription'"
    },
    {
        "number": 2,
        "name": "Etat civil - Informations de base",
        "fields": {
            "nom_naissance": {"required": True, "format": "Texte en MAJUSCULES"},
            "nom_usuel": {"required": False, "format": "Texte en MAJUSCULES (optionnel)"},
            "prenom_1": {"required": True, "format": "Texte en MAJUSCULES"},
            "prenom_2": {"required": False, "format": "Texte en MAJUSCULES (optionnel)"},
            "prenom_3": {"required": False, "format": "Texte en MAJUSCULES (optionnel)"},
            "numero_etudiant": {
                "required": False, 
                "format": "8 caractères",
                "condition": "Réinscription uniquement",
                "help": "N° Etudiant (8 caractères si réinscription). Si c'est votre première inscription, vous n'avez pas encore de numéro étudiant.",
                "where_to_find": "Si vous êtes en réinscription, ce numéro figure sur votre carte étudiante de l'année précédente."
            },
            "numero_ines": {
                "required": True, 
                "format": "11 caractères",
                "help": "N° INES (11 caractères). Bachelier : le numéro figure sur le relevé de notes du baccalauréat (N° INES/INE/BEA). Tout étudiant ayant pris une inscription dans une université française depuis 1995 dispose obligatoirement d'un N° INE/INES. S'il ne figure pas sur la carte d'étudiant, l'intéressé doit le demander à son établissement d'origine avant de s'inscrire à Aix-Marseille Université.",
                "where_to_find": "Sur votre relevé de notes du baccalauréat (N° INES/INE/BEA) ou sur votre carte d'étudiant si vous avez déjà été inscrit dans une université française depuis 1995.",
                "note": "⚠️ IMPORTANT : Le N° INES est demandé pour TOUS les étudiants, même en première inscription. Il figure sur le relevé de notes du baccalauréat."
            }
        },
        "required": True
    },
    {
        "number": 3,
        "name": "Date de naissance et sexe",
        "fields": {
            "date_naissance": {"required": True, "format": "JJ/MM/AAAA"},
            "sexe": {"required": True, "type": "choice", "options": ["M.", "F."], "format": "M. ou F."}
        },
        "required": True
    },
    {
        "number": 4,
        "name": "Lieu de naissance",
        "fields": {
            "ville_naissance": {"required": True, "format": "Texte"},
            "arrondissement": {"required": False, "format": "Si Paris, Marseille ou Lyon"},
            "departement_naissance": {"required": True, "format": "Code département (annexe 1)"},
            "pays_naissance": {"required": True, "format": "Code pays (annexe 2, France = 100)"}
        },
        "required": True
    },
    {
        "number": 5,
        "name": "Nationalité",
        "fields": {
            "nationalite": {"required": True, "format": "Code pays (annexe 2, France = 100)"},
            "refugie_politique": {"required": False, "type": "checkbox", "format": "Oui/Non"}
        },
        "required": True
    },
    {
        "number": 6,
        "name": "Situation familiale",
        "field": "situation_familiale",
        "required": True,
        "type": "choice",
        "options": [
            "1 - Seul sans enfant",
            "2 - En couple sans enfant",
            "3 - Seul avec enfant(s)",
            "4 - En couple avec enfant(s)"
        ],
        "format": "Choisir 1, 2, 3 ou 4",
        "additional_field": "nombre_enfants",
        "additional_required": False,
        "additional_format": "Nombre d'enfants à charge (si applicable)"
    },
    {
        "number": 7,
        "name": "Handicap",
        "field": "handicap",
        "required": False,
        "type": "info",
        "format": "Information sur le régime spécial d'études (optionnel)"
    },
    {
        "number": 8,
        "name": "Situation militaire",
        "field": "situation_militaire",
        "required": True,
        "type": "choice",
        "options": [
            "3 - Exempté",
            "4 - Service accompli",
            "5 - Attestation de recensement (- 18 ans)",
            "6 - Certificat de participation à la JDC fourni (+ 18 ans)",
            "7 - Attente certificat de participation à la JDC"
        ],
        "format": "Choisir 3, 4, 5, 6 ou 7"
    },
    {
        "number": 9,
        "name": "Première inscription dans l'enseignement supérieur français",
        "fields": {
            "premiere_inscription_sup_annee": {"required": False, "format": "Année (si applicable)"},
            "premiere_inscription_universite_annee": {"required": False, "format": "Année (si applicable)"},
            "premiere_inscription_universite_etablissement": {"required": False, "format": "Code établissement (annexe 3, AMU = 0134009M)"}
        },
        "required": True
    },
    {
        "number": 10,
        "name": "Baccalauréat français ou équivalence",
        "fields": {
            "bac_annee": {"required": True, "format": "Année d'obtention"},
            "bac_serie": {"required": True, "format": "Série ou équivalence (code annexe 4)"},
            "bac_mention": {"required": False, "format": "Mention (optionnel)"},
            "bac_specialite_1_terminale": {"required": False, "format": "Si BAC 2021+, Spécialité 1 de Terminale"},
            "bac_specialite_2_terminale": {"required": False, "format": "Si BAC 2021+, Spécialité 2 de Terminale"},
            "bac_specialite_premiere_abandonnee": {"required": False, "format": "Spécialité de Première abandonnée"},
            "bac_type_etablissement": {"required": True, "type": "choice", "options": ["LY - Lycée", "00 - Université", "Autre"], "format": "Type d'établissement"},
            "bac_nom_etablissement": {"required": True, "format": "Nom de l'établissement"},
            "bac_ville": {"required": True, "format": "Ville"},
            "bac_departement": {"required": True, "format": "Code département (annexe 1, 099 si étranger)"}
        },
        "required": True
    },
    {
        "number": 11,
        "name": "Adresses",
        "fields": {
            "adresse_complete": {"required": True, "format": "Adresse complète"},
            "code_postal": {"required": True, "format": "5 chiffres"},
            "ville": {"required": True, "format": "Ville"},
            "type_hebergement": {
                "required": True,
                "type": "choice",
                "options": [
                    "1 - Résidence universitaire",
                    "2 - Foyer agréé",
                    "3 - Logement HLM CROUS",
                    "4 - Domicile parental",
                    "5 - Logement personnel (hors chambre étudiant)",
                    "6 - Chambre étudiant",
                    "7 - Autre mode d'hébergement"
                ],
                "format": "Choisir 1, 2, 3, 4, 5, 6 ou 7"
            }
        },
        "required": True
    },
    {
        "number": 12,
        "name": "Inscription administrative annuelle - Catégorie socio-professionnelle de l'étudiant",
        "fields": {
            "csp_etudiant_code": {"required": True, "format": "Code CSP (annexe 5)"},
            "csp_etudiant_activite": {
                "required": True,
                "type": "choice",
                "options": [
                    "Inactivité",
                    "Demandeur d'emploi indemnisé",
                    "Demandeur d'emploi non indemnisé",
                    "CDD",
                    "CDI"
                ],
                "format": "Choisir parmi les options"
            },
            "csp_etudiant_quotite": {
                "required": True,
                "type": "choice",
                "options": [
                    "Temps complet",
                    "Temps partiel supérieur au mi-temps",
                    "Temps partiel inférieur ou égal au mi-temps"
                ],
                "format": "Choisir parmi les options"
            }
        },
        "required": True
    },
    {
        "number": 13,
        "name": "Inscription administrative annuelle - Catégorie socio-professionnelle des parents",
        "fields": {
            "csp_parent_1": {"required": True, "format": "Code CSP premier parent (annexe 5)"},
            "csp_parent_2": {"required": True, "format": "Code CSP second parent (annexe 5)"}
        },
        "required": True
    },
    {
        "number": 14,
        "name": "Sportif de haut niveau",
        "field": "sportif_haut_niveau",
        "required": False,
        "type": "choice",
        "options": ["National", "Régional", "Universitaire"],
        "format": "National, Régional ou Universitaire (optionnel)"
    },
    {
        "number": 15,
        "name": "Aides financières autres que bourse sur critères sociaux",
        "field": "aides_financieres",
        "required": False,
        "format": "Détails des aides (optionnel)"
    },
    {
        "number": 16,
        "name": "Échanges internationaux",
        "fields": {
            "echanges_internationaux": {
                "required": True,
                "type": "choice",
                "options": ["Oui", "Non"],
                "format": "Oui ou Non"
            },
            "echanges_type": {
                "required": False,
                "type": "choice",
                "options": ["Départ", "Arrivée (dans l'établissement)"],
                "format": "Si Oui, Départ ou Arrivée"
            },
            "echanges_programme": {
                "required": False,
                "type": "choice",
                "options": ["Erasmus", "Autres programmes"],
                "format": "Erasmus ou Autres programmes"
            },
            "echanges_etablissement_etranger": {"required": False, "format": "Nom établissement étranger"},
            "echanges_pays": {"required": False, "format": "Code pays (annexe 2)"}
        },
        "required": True
    },
    {
        "number": 17,
        "name": "Dernier établissement fréquenté",
        "fields": {
            "dernier_etablissement_annee": {"required": True, "format": "Année de la dernière inscription"},
            "dernier_etablissement_francais_nom": {"required": False, "format": "Code établissement (annexe 3)"},
            "dernier_etablissement_francais_departement": {"required": False, "format": "Code département (annexe 1)"},
            "dernier_etablissement_etranger_nom": {"required": False, "format": "Nom établissement étranger"},
            "dernier_etablissement_etranger_pays": {"required": False, "format": "Code pays (annexe 2)"}
        },
        "required": True
    },
    {
        "number": 18,
        "name": "Situation de l'année 2025-2026",
        "fields": {
            "situation_2025_2026_type": {
                "required": True,
                "type": "choice",
                "options": ["T", "U", "Q", "R"],
                "format": "T, U, Q ou R (selon situation)"
            },
            "situation_etablissement_francais_nom": {"required": False, "format": "Code établissement (annexe 3)"},
            "situation_etablissement_francais_departement": {"required": False, "format": "Code département (annexe 1)"},
            "situation_etablissement_etranger_nom": {"required": False, "format": "Nom établissement étranger"},
            "situation_etablissement_etranger_pays": {"required": False, "format": "Code pays (annexe 2)"}
        },
        "required": True
    },
    {
        "number": 19,
        "name": "Dernier diplôme obtenu",
        "fields": {
            "dernier_diplome_code": {"required": True, "format": "Code diplôme (annexe 6)"},
            "dernier_diplome_libelle": {"required": True, "format": "Libellé du diplôme"},
            "dernier_diplome_annee": {"required": True, "format": "Année d'obtention"},
            "dernier_diplome_etablissement": {"required": True, "format": "Code établissement (annexe 3)"},
            "dernier_diplome_departement": {"required": False, "format": "Code département (annexe 1)"},
            "dernier_diplome_pays": {"required": False, "format": "Code pays (annexe 2)"}
        },
        "required": True
    },
    {
        "number": 20,
        "name": "Inscrit dans un autre établissement cette année",
        "fields": {
            "inscrit_autre_etablissement": {
                "required": True,
                "type": "choice",
                "options": ["Oui", "Non"],
                "format": "Oui ou Non"
            },
            "autre_etablissement_nom": {"required": False, "format": "Code établissement (annexe 3)"},
            "autre_etablissement_ville": {"required": False, "format": "Ville"}
        },
        "required": True
    },
    {
        "number": 21,
        "name": "Diplômes et étapes postulés - Principal",
        "fields": {
            "diplome_postule_intitule": {"required": True, "format": "Intitulé du diplôme (ex: Licence de Droit)"},
            "diplome_postule_specialite": {"required": True, "format": "Spécialité"},
            "diplome_postule_finalite": {
                "required": True,
                "type": "choice",
                "options": ["Recherche", "Professionnelle"],
                "format": "Recherche ou Professionnelle"
            },
            "diplome_postule_parcours": {"required": True, "format": "Parcours"},
            "diplome_postule_niveau": {"required": True, "format": "Niveau année (ex: 1ère année)"},
            "diplome_postule_code_etape": {"required": False, "format": "Code étape (réservé à l'administration)"},
            "diplome_postule_lieu": {"required": False, "format": "Lieu choisi (si plusieurs sites)"},
            "diplome_postule_nb_inscriptions_cycle": {"required": True, "format": "Nombre d'inscriptions dans le cycle"},
            "diplome_postule_nb_inscriptions_diplome": {"required": True, "format": "Nombre d'inscriptions dans le diplôme"},
            "diplome_postule_nb_inscriptions_niveau": {"required": True, "format": "Nombre d'inscriptions dans le niveau (étape)"},
            "diplome_postule_code_cpge": {"required": False, "format": "Code CPGE (annexe 7, si applicable)"},
            "diplome_postule_cesure": {
                "required": False,
                "type": "choice",
                "options": ["code 3 - annuelle", "code 4 - semestrielle"],
                "format": "Si étudiant césure"
            },
            "diplome_postule_enseignement_distance": {
                "required": True,
                "type": "choice",
                "options": ["Oui", "Non"],
                "format": "Oui ou Non"
            },
            "diplome_postule_enseignement_distance_lieu": {
                "required": False,
                "type": "choice",
                "options": ["France", "L'étranger"],
                "format": "Si Oui, depuis la France ou l'étranger"
            },
            "diplome_postule_bourses": {"required": False, "format": "Bourses octroyées pour ce diplôme"},
            "diplome_postule_these_cotutelle": {
                "required": False,
                "type": "choice",
                "options": ["Oui", "Non"],
                "format": "Thèse en cotutelle"
            }
        },
        "required": True
    },
    {
        "number": 22,
        "name": "Diplômes et étapes postulés - Autre diplôme (optionnel)",
        "fields": {
            "autre_diplome_postule_intitule": {"required": False, "format": "Intitulé"},
            "autre_diplome_postule_etape": {"required": False, "format": "Etape (année)"},
            "autre_diplome_postule_code_etape": {"required": False, "format": "Code étape"},
            "autre_diplome_postule_lieu": {"required": False, "format": "Lieu choisi"},
            "autre_diplome_postule_nb_inscriptions_cycle": {"required": False, "format": "Nombre d'inscriptions dans le cycle"},
            "autre_diplome_postule_nb_inscriptions_diplome": {"required": False, "format": "Nombre d'inscriptions dans le diplôme"},
            "autre_diplome_postule_nb_inscriptions_niveau": {"required": False, "format": "Nombre d'inscriptions dans le niveau"},
            "autre_diplome_postule_enseignement_distance": {
                "required": False,
                "type": "choice",
                "options": ["Oui", "Non"],
                "format": "Enseignement à distance"
            },
            "autre_diplome_postule_enseignement_distance_lieu": {
                "required": False,
                "type": "choice",
                "options": ["France", "L'étranger"],
                "format": "Si Oui, depuis la France ou l'étranger"
            }
        },
        "required": False
    },
    {
        "number": 23,
        "name": "Informations complémentaires",
        "fields": {
            "pupilles_nation": {
                "required": True,
                "type": "choice",
                "options": ["Oui", "Non"],
                "format": "Oui ou Non"
            },
            "assurance_responsabilite_civile": {
                "required": True,
                "type": "choice",
                "options": ["Affiliation en cours", "Non"],
                "format": "Affiliation en cours ou Non"
            },
            "assurance_organisme": {"required": False, "format": "Préciser l'organisme (si affiliation)"},
            "etudiant_mineur": {
                "required": True,
                "type": "choice",
                "options": ["Oui", "Non"],
                "format": "Oui ou Non"
            }
        },
        "required": True
    },
    {
        "number": 24,
        "name": "Certifications et signature",
        "fields": {
            "certification_exactitude": {
                "required": True,
                "type": "checkbox",
                "format": "Case à cocher obligatoire"
            },
            "certification_charte": {
                "required": True,
                "type": "checkbox",
                "format": "Case à cocher obligatoire - Prise de connaissance de la charte"
            },
            "signature_date": {"required": True, "format": "Date de signature (JJ/MM/AAAA)"},
            "signature_lieu": {"required": True, "format": "Lieu de signature"}
        },
        "required": True
    }
]


def get_all_required_fields(inscription_type: str = None) -> List[str]:
    """Retourne la liste de tous les champs obligatoires"""
    required_fields = []
    for section in FORM_SECTIONS:
        if section.get("required", True):
            if "field" in section:
                # Section simple avec un seul champ
                required_fields.append(section["field"])
            elif "fields" in section:
                # Section avec plusieurs champs
                for field_name, field_info in section["fields"].items():
                    if field_info.get("required", True):
                        required_fields.append(field_name)
    return required_fields


def get_missing_sections(form_data: Dict) -> List[Dict]:
    """Retourne la liste des sections manquantes dans form_data"""
    missing = []
    for section in FORM_SECTIONS:
        if not section.get("required", True):
            continue
        
        section_missing = False
        missing_fields = []
        
        if "field" in section:
            # Section simple
            field = section["field"]
            if field not in form_data or not form_data.get(field):
                section_missing = True
                missing_fields.append(field)
        elif "fields" in section:
            # Section avec plusieurs champs
            for field_name, field_info in section["fields"].items():
                if field_info.get("required", True):
                    if field_name not in form_data or not form_data.get(field_name):
                        section_missing = True
                        missing_fields.append(field_name)
        
        if section_missing:
            section_copy = section.copy()
            section_copy["missing_fields"] = missing_fields
            missing.append(section_copy)
    
    return missing


def is_form_complete(form_data: Dict) -> bool:
    """Vérifie si toutes les sections requises sont remplies"""
    missing = get_missing_sections(form_data)
    return len(missing) == 0


def get_section_by_number(number: int) -> Optional[Dict]:
    """Retourne une section par son numéro"""
    for section in FORM_SECTIONS:
        if section["number"] == number:
            return section
    return None


def get_section_by_field(field_name: str) -> Optional[Dict]:
    """Retourne une section par le nom d'un de ses champs"""
    for section in FORM_SECTIONS:
        if "field" in section and section["field"] == field_name:
            return section
        elif "fields" in section:
            if field_name in section["fields"]:
                return section
    return None
