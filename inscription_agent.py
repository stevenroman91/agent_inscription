"""
Agent intelligent pour guider les étudiants dans le processus d'inscription
"""
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
try:
    from langchain.agents import initialize_agent, AgentType
    from langchain.tools import Tool
    from langchain.memory import ConversationBufferMemory
except ImportError:
    from langchain_classic.agents import initialize_agent, AgentType
    from langchain_classic.tools import Tool
    from langchain_classic.memory import ConversationBufferMemory
from rag_system import RAGSystem
from form_sections import FORM_SECTIONS, get_missing_sections, is_form_complete, get_section_by_field
from field_detection import get_field_info, requires_code, get_annexe_number, is_choice_field, get_choice_options


class InscriptionAgent:
    """Agent intelligent pour aider avec les inscriptions"""
    
    def __init__(self, rag_system: RAGSystem, openai_api_key: str, profile_manager=None):
        self.rag_system = rag_system
        self.profile_manager = profile_manager
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.3,
            api_key=openai_api_key
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialise l'agent avec les outils appropriés"""
        
        # Outil pour poser des questions au RAG
        rag_tool = Tool(
            name="ConsultationDocuments",
            func=lambda q: self.rag_system.query(q)["answer"],
            description="Utilise cet outil pour consulter les documents officiels d'inscription (dossier, pièces à fournir, codes, annexes). Utilise-le quand tu as besoin d'informations précises sur le processus d'inscription. ⚠️ IMPORTANT : Si un champ nécessite un code d'annexe (ex: code département, code pays, code établissement), utilise cet outil pour obtenir la liste des codes disponibles depuis les annexes."
        )
        
        # Outil pour obtenir les codes
        codes_tool = Tool(
            name="ObtenirCodes",
            func=lambda category: self.rag_system.get_codes(category)["answer"],
            description="Utilise cet outil pour obtenir les codes d'inscription depuis les annexes. L'étudiant peut demander des codes pour une catégorie spécifique."
        )
        
        # Outil pour vérifier les pièces à fournir (DÉSACTIVÉ en Phase 2)
        def check_documents_wrapper(query: str) -> str:
            """Vérifie les documents - DÉSACTIVÉ en Phase 2"""
            # Cet outil ne doit JAMAIS être utilisé en Phase 2
            return "⚠️ CET OUTIL EST DÉSACTIVÉ. Les documents ont déjà été identifiés en Phase 1. En Phase 2, concentre-toi uniquement sur le remplissage du formulaire."
        
        documents_tool = Tool(
            name="VerifierPieces",
            func=check_documents_wrapper,
            description="⚠️⚠️⚠️ INTERDIT EN PHASE 2 : N'utilise JAMAIS cet outil si la phase est 'remplissage_formulaire'. Les documents ont déjà été identifiés. Concentre-toi uniquement sur le remplissage du formulaire."
        )
        
        # Outil pour aider avec un champ spécifique
        form_help_tool = Tool(
            name="AideChampFormulaire",
            func=lambda field: self.rag_system.help_with_form_field(field)["answer"],
            description="🚨 IMPORTANT : Utilise cet outil AVANT de poser une question sur un champ du formulaire. Il te donne toutes les informations du dossier d'inscription : le format attendu, où trouver l'information, les conditions (ex: uniquement pour réinscription), le nombre de caractères, etc. Utilise ces informations pour aider l'étudiant de manière précise et utile."
        )
        
        # Outil pour consulter le profil de l'étudiant
        def get_profile_info_wrapper(session_id_str: str) -> str:
            """Récupère les informations du profil étudiant"""
            if not self.profile_manager:
                return "Aucun gestionnaire de profil disponible"
            
            # Extraire le session_id du format [SESSION_ID: xxx] ou directement
            session_id = session_id_str.strip()
            if "[SESSION_ID:" in session_id:
                # Extraire le session_id du message
                start = session_id.find("[SESSION_ID:") + len("[SESSION_ID:")
                end = session_id.find("]", start)
                if end > start:
                    session_id = session_id[start:end].strip()
                else:
                    return "Format de session_id invalide"
            
            if not session_id:
                return "Aucun session_id fourni"
            
            profile = self.profile_manager.load_profile(session_id)
            if not profile:
                return "Aucun profil trouvé pour cette session"
            
            info = f"PROFIL ÉTUDIANT:\n"
            info += f"- Type d'inscription: {profile.inscription_type or 'Non défini'}\n"
            info += f"  ⚠️ IMPORTANT : Si 'Type d'inscription' = 'premiere_inscription', l'étudiant est en PREMIÈRE INSCRIPTION → NE PAS demander le N° étudiant (il n'en a pas encore)\n"
            info += f"  ⚠️ IMPORTANT : Si 'Type d'inscription' = 'lap', 'master', ou 'prep_concours', l'étudiant est en RÉINSCRIPTION → tu PEUX demander le N° étudiant\n"
            info += f"- Boursier: {profile.is_boursier if profile.is_boursier is not None else 'Non défini'}\n"
            info += f"- Mineur: {profile.is_mineur if profile.is_mineur is not None else 'Non défini'}\n"
            info += f"- Inscrit ailleurs: {profile.inscrit_autre_etablissement if profile.inscrit_autre_etablissement is not None else 'Non défini'}\n"
            info += f"- JDC fournie: {profile.has_jdc if profile.has_jdc is not None else 'Non défini'}\n"
            info += f"- Phase actuelle: {profile.phase}\n"
            if profile.required_documents:
                info += f"- Documents requis: {len(profile.required_documents)} documents identifiés\n"
            
            # Ajouter les données du formulaire si disponibles
            if profile.form_data:
                info += f"\n🚨🚨🚨 DONNÉES DU FORMULAIRE DÉJÀ COLLECTÉES 🚨🚨🚨:\n"
                info += "⚠️ ATTENTION : Si un champ est listé ci-dessous, NE JAMAIS redemander cette information !\n"
                info += "⚠️ Utilise ces données pour passer directement à la question suivante !\n\n"
                has_data = False
                for key, value in profile.form_data.items():
                    if value:  # Ne montrer que les champs remplis
                        info += f"✅ {key}: {value}\n"
                        has_data = True
                if not has_data:
                    info += "- Aucune donnée collectée pour le moment\n"
                info += "\n⚠️ RAPPEL : Si tu vois un champ ci-dessus, NE PAS redemander cette information !\n"
            else:
                info += f"\nDONNÉES DU FORMULAIRE: Aucune donnée collectée pour le moment\n"
            
            # ⚠️ IMPORTANT : Le type d'inscription est déjà collecté en Phase 1
            if profile.inscription_type:
                if profile.inscription_type == "premiere_inscription":
                    info += f"\n⚠️⚠️⚠️ TYPE D'INSCRIPTION DÉJÀ COLLECTÉ EN PHASE 1 ⚠️⚠️⚠️:\n"
                    info += f"✅ type_inscription: 1ère Inscription (déjà collecté en Phase 1)\n"
                    info += f"🚨 NE PAS redemander le type d'inscription - il est déjà dans form_data ou correspond à inscription_type du profil\n"
                elif profile.inscription_type in ["lap", "master", "prep_concours"]:
                    info += f"\n⚠️⚠️⚠️ TYPE D'INSCRIPTION DÉJÀ COLLECTÉ EN PHASE 1 ⚠️⚠️⚠️:\n"
                    info += f"✅ type_inscription: Réinscription (déjà collecté en Phase 1)\n"
                    info += f"🚨 NE PAS redemander le type d'inscription - il est déjà dans form_data ou correspond à inscription_type du profil\n"
            
            return info
        
        profile_tool = Tool(
            name="ConsulterProfil",
            func=get_profile_info_wrapper,
            description="🚨🚨🚨 OBLIGATOIRE - UTILISE CET OUTIL EN PREMIER AVANT TOUTE RÉPONSE 🚨🚨🚨\n\nTu DOIS utiliser cet outil AVANT de poser une question ou de répondre à l'étudiant. Passe le session_id (qui est dans le message entre [SESSION_ID: ...]).\n\nCet outil te donne:\n- La phase actuelle (collecte_info ou remplissage_formulaire)\n- Les données du formulaire DÉJÀ COLLECTÉES dans la section 'DONNÉES DU FORMULAIRE DÉJÀ COLLECTÉES'\n\n⚠️⚠️⚠️ RÈGLE ABSOLUE :\n- Si tu vois un champ dans 'DONNÉES DU FORMULAIRE DÉJÀ COLLECTÉES', NE JAMAIS redemander cette information\n- Exemple : Si tu vois 'nom_naissance: Roman', NE DEMANDE PAS le nom de famille\n- Exemple : Si tu vois 'prenom_1: Steven', NE DEMANDE PAS le prénom\n- Utilise les données déjà collectées pour passer directement à la question suivante\n\nSi la phase est 'remplissage_formulaire', tu es en Phase 2 et tu dois UNIQUEMENT aider à remplir le formulaire, SANS mentionner les documents."
        )
        
        # Outil pour sauvegarder les données du formulaire
        def save_form_data_wrapper(data_str: str) -> str:
            """Sauvegarde les données du formulaire"""
            if not self.profile_manager:
                return "Aucun gestionnaire de profil disponible"
            
            # Le format attendu est "session_id|field:value" ou "session_id|field1:value1,field2:value2"
            # On extrait le session_id et les données
            try:
                # Format simplifié : on attend que le session_id soit dans le message contextuel
                # Pour l'instant, on retourne juste un message indiquant que les données doivent être sauvegardées
                # La sauvegarde sera gérée par le frontend
                return "Les données seront sauvegardées automatiquement. Continue avec la question suivante."
            except Exception as e:
                return f"Erreur lors de la sauvegarde: {str(e)}"
        
        save_form_tool = Tool(
            name="SauvegarderDonneesFormulaire",
            func=save_form_data_wrapper,
            description="⚠️ Utilise cet outil APRÈS avoir collecté une réponse de l'étudiant pour un champ du formulaire. Format: 'nom:Roman' ou 'prenom:Steven' ou 'email:test@example.com' ou 'numero_etudiant:12345678'. Les données seront sauvegardées automatiquement. Utilise cet outil après chaque réponse de l'étudiant pour un champ du formulaire. ⚠️ IMPORTANT : Si l'étudiant donne une réponse numérique simple (ex: '12345678' pour le numéro d'étudiant), accepte-la et sauvegarde-la directement."
        )
        
        # Outil pour vérifier les sections manquantes
        def check_missing_sections_wrapper(session_id_str: str) -> str:
            """Vérifie quelles sections du formulaire sont manquantes"""
            if not self.profile_manager:
                return "Aucun gestionnaire de profil disponible"
            
            # Extraire le session_id
            session_id = session_id_str.strip()
            if "[SESSION_ID:" in session_id:
                start = session_id.find("[SESSION_ID:") + len("[SESSION_ID:")
                end = session_id.find("]", start)
                if end > start:
                    session_id = session_id[start:end].strip()
            
            if not session_id:
                return "Aucun session_id fourni"
            
            profile = self.profile_manager.load_profile(session_id)
            if not profile:
                return "Aucun profil trouvé"
            
            missing = get_missing_sections(profile.form_data or {})
            if not missing:
                return "✅ Toutes les sections obligatoires sont remplies ! Le formulaire est complet."
            
            # Vérifier le type d'inscription pour filtrer les champs conditionnels
            inscription_type = profile.inscription_type
            
            info = f"📋 CHAMPS MANQUANTS À REMPLIR:\n\n"
            
            # Grouper par section et lister les champs manquants
            for section in missing:
                info += f"Section {section['number']}: {section['name']}\n"
                
                if "missing_fields" in section:
                    for field_name in section["missing_fields"]:
                        # Vérifier si le champ est conditionnel
                        field_info = None
                        if "fields" in section and field_name in section["fields"]:
                            field_info = section["fields"][field_name]
                        elif "field" in section and section["field"] == field_name:
                            field_info = section
                        
                        if field_info:
                            condition = field_info.get("condition", "")
                            help_text = field_info.get("help", "")
                            format_text = field_info.get("format", "")
                            
                            # Vérifier si le champ doit être demandé selon le type d'inscription
                            should_ask = True
                            if condition and "réinscription" in condition.lower():
                                if inscription_type == "premiere_inscription":
                                    should_ask = False
                                    info += f"  ⏭️ {field_name}: NON DEMANDÉ (condition: {condition})\n"
                            
                            if should_ask:
                                info += f"  ❌ {field_name}"
                                if format_text:
                                    info += f" (format: {format_text})"
                                if help_text:
                                    info += f"\n     💡 {help_text[:100]}..."
                                info += "\n"
                else:
                    # Section simple avec un seul champ
                    field = section.get("field", "")
                    format_text = section.get("format", "")
                    info += f"  ❌ {field}"
                    if format_text:
                        info += f" (format: {format_text})"
                    info += "\n"
                
                info += "\n"
            
            info += f"⚠️ IMPORTANT : Pour chaque champ manquant ci-dessus, utilise AideChampFormulaire pour obtenir les informations détaillées du dossier d'inscription avant de le demander à l'étudiant.\n"
            info += f"⚠️ Tu dois remplir TOUS ces champs avant de dire que le formulaire est complet."
            
            return info
        
        check_sections_tool = Tool(
            name="VerifierSectionsManquantes",
            func=check_missing_sections_wrapper,
            description="🚨 OBLIGATOIRE: Utilise cet outil pour savoir quels champs du formulaire sont encore manquants. Passe le session_id (qui est dans le message entre [SESSION_ID: ...]). Il te liste TOUS les champs manquants avec leur format et leurs conditions. Pour chaque champ manquant, utilise ensuite AideChampFormulaire pour obtenir les informations détaillées du dossier d'inscription. Ne dis JAMAIS que le formulaire est complet tant que cet outil ne confirme pas qu'il ne manque plus aucun champ obligatoire."
        )
        
        tools = [profile_tool, rag_tool, codes_tool, documents_tool, form_help_tool, save_form_tool, check_sections_tool]
        
        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            agent_kwargs={
                "system_message": """Tu es un assistant spécialisé dans l'aide aux inscriptions à Sciences Po Aix. 
Ton rôle est de guider les étudiants à travers DEUX PHASES distinctes.

🚨🚨🚨 RÈGLE CRITIQUE ABSOLUE - OBLIGATOIRE AVANT TOUTE RÉPONSE 🚨🚨🚨 :
1. Vérifie si le message contient [ACCOUNT_EMAIL: xxx@xxx.com] - cela signifie que l'étudiant est connecté avec ce compte
2. 🚨 UTILISE OBLIGATOIREMENT l'outil ConsulterProfil EN PREMIER - C'EST OBLIGATOIRE, PAS OPTIONNEL 🚨
   - Tu DOIS appeler ConsulterProfil AVANT de poser une question
   - Tu DOIS appeler ConsulterProfil AVANT de répondre à l'étudiant
   - Tu DOIS appeler ConsulterProfil APRÈS avoir reçu une réponse de l'étudiant pour vérifier que les données ont été sauvegardées
   - ConsulterProfil te montre les données DÉJÀ COLLECTÉES dans 'DONNÉES DU FORMULAIRE DÉJÀ COLLECTÉES'
   - Si un champ est déjà dans les données collectées, NE JAMAIS redemander cette information
   - ⚠️ CRITIQUE : Si tu vois "ville_naissance: Piura" dans les données collectées, NE DEMANDE PAS la ville de naissance, passe au champ suivant
   - 🚨 INTERDIT : NE JAMAIS inventer ou supposer des informations qui ne sont pas dans ConsulterProfil
   - 🚨 INTERDIT : NE JAMAIS dire "D'après les informations déjà collectées, votre nom est X" si X n'est pas dans les données collectées
   - 🚨 INTERDIT : NE JAMAIS extraire des informations de l'email du compte pour remplir le formulaire
   - Si ConsulterProfil ne montre PAS de données pour un champ, alors ce champ n'a PAS encore été collecté
3. Si tu es en Phase 2, utilise TOUJOURS l'outil VerifierSectionsManquantes pour savoir quelles sections manquent encore

PHASE 1 - COLLECTE D'INFORMATIONS (phase = "collecte_info") :
Cette phase est gérée par le système, tu n'as pas besoin d'intervenir ici.

PHASE 2 - REMPLISSAGE DU FORMULAIRE (phase = "remplissage_formulaire") :
🚫🚫🚫 INTERDICTIONS ABSOLUES EN PHASE 2 :
- NE JAMAIS mentionner les documents nécessaires
- NE JAMAIS dire "vous devez fournir les documents suivants"
- NE JAMAIS dire "D'après votre profil, vous devez fournir..."
- NE JAMAIS utiliser l'outil VerifierPieces
- NE JAMAIS répéter la liste des documents
- NE JAMAIS mentionner "9 documents déjà identifiés" ou similaire

✅ CE QUE TU DOIS FAIRE EN PHASE 2 :
- 🚨 OBLIGATOIRE : AVANT de poser une question, utilise TOUJOURS l'outil ConsulterProfil pour vérifier les données déjà collectées
- 🚨 OBLIGATOIRE : Regarde la section "DONNÉES DU FORMULAIRE DÉJÀ COLLECTÉES" dans le résultat de ConsulterProfil
- 🚨 OBLIGATOIRE : Utilise l'outil VerifierSectionsManquantes pour savoir quels champs manquent encore
- 🚨 OBLIGATOIRE : Pour chaque champ manquant, utilise AideChampFormulaire pour comprendre comment le remplir
- 🚨 INTERDIT : NE JAMAIS redemander une information déjà présente dans "DONNÉES DU FORMULAIRE DÉJÀ COLLECTÉES"
  - Si tu vois "nom_naissance: Roman" → NE DEMANDE PAS le nom de naissance, passe au champ suivant
  - ⚠️ IMPORTANT : Le formulaire officiel demande le "Nom de naissance" (terminologie officielle)
  - "nom de famille" et "nom de naissance" sont DES SYNONYMES pour le même champ "nom_naissance"
  - Si tu as déjà demandé le "nom de naissance" (ou "nom de famille") et que l'étudiant a répondu, NE PAS redemander (c'est le même champ)
  - Si tu vois "prenom_1: Steven" → NE DEMANDE PAS le prénom, passe au champ suivant
  - Si tu vois "email: test@example.com" → NE DEMANDE PAS l'email, passe au champ suivant
- 🚨 INTERDIT : NE JAMAIS inventer des informations qui ne sont pas dans ConsulterProfil
  - Si ConsulterProfil ne montre PAS un champ, alors ce champ n'a PAS été collecté → tu DOIS le demander
  - NE JAMAIS dire "D'après les informations déjà collectées, votre nom est X" si "nom_naissance: X" n'est PAS dans les données collectées
  - NE JAMAIS extraire des informations de l'email du compte (comme "sroman" → "Steven") pour remplir le formulaire
- 🚨 UTILISE LES DOCUMENTS D'INSCRIPTION - NE TE BASE PAS sur des instructions hardcodées
  - Utilise VerifierSectionsManquantes pour savoir quels champs manquent
  - Utilise AideChampFormulaire pour chaque champ avant de le demander
  - Les documents te diront : quels champs sont obligatoires, quels sont optionnels, quels sont conditionnels, où trouver les informations, etc.
  - Tu dois remplir TOUS les champs obligatoires avant de dire que le formulaire est complet
  - Concentre-toi UNIQUEMENT sur le remplissage du formulaire
  - Pose des questions UNE PAR UNE pour chaque champ MANQUANT dans l'ordre logique

📝 RÈGLES POUR LES DIFFÉRENTS TYPES DE CHAMPS :
- 🚨 AVANT de poser une question sur un champ, utilise TOUJOURS l'outil AideChampFormulaire pour obtenir les informations détaillées du dossier d'inscription
  - L'outil AideChampFormulaire te donne : le format attendu, où trouver l'information, les conditions, etc.
  - ⚠️ IMPORTANT : Si AideChampFormulaire indique qu'un champ nécessite un CODE d'annexe, utilise l'outil ObtenirCodes pour obtenir la liste des codes disponibles
  - Exemple : Si le champ "département de naissance" nécessite un code d'annexe 1, utilise ObtenirCodes pour obtenir la liste des codes départements
  - Utilise ces informations pour aider l'étudiant de manière précise et utile
  - NE TE BASE PAS sur des instructions hardcodées - utilise les informations du document d'inscription
- 🚨 UTILISE l'outil VerifierSectionsManquantes pour savoir quels champs manquent encore
  - Cet outil te dit exactement quels champs sont manquants dans le formulaire
  - Demande les champs manquants UN PAR UN dans l'ordre logique
  - Pour chaque champ manquant, utilise AideChampFormulaire pour savoir comment le remplir
  - Si le champ nécessite un code d'annexe, utilise ObtenirCodes pour obtenir les codes disponibles
- Pour les champs de type "choice" : Présente TOUJOURS toutes les options disponibles dans le format EXACT : "(1 - Option 1, 2 - Option 2, 3 - Option 3, 4 - Option 4)"
  Exemple : "Quelle est votre situation familiale ? (1 - Seul sans enfant, 2 - En couple sans enfant, 3 - Seul avec enfant(s), 4 - En couple avec enfant(s))"
  ⚠️ IMPORTANT : Utilise TOUJOURS ce format avec parenthèses et tirets pour que le frontend puisse détecter les choix multiples
- Pour les sections avec plusieurs champs : Utilise VerifierSectionsManquantes et AideChampFormulaire pour savoir quels champs sont obligatoires et dans quel ordre
  - NE TE BASE PAS sur des listes hardcodées - consulte les documents
  - Pour chaque champ manquant, utilise AideChampFormulaire pour comprendre :
    * Si le champ est obligatoire ou optionnel
    * Si le champ est conditionnel (ex: uniquement pour réinscription)
    * Où trouver l'information
    * Le format attendu
- Pour les checkboxes : Demande une confirmation claire (Oui/Non)
  Exemple : "Certifiez-vous sur l'honneur l'exactitude des renseignements fournis ? (Oui/Non)"
- Pour les champs conditionnels : Utilise AideChampFormulaire pour savoir si un champ est conditionnel
  - Si AideChampFormulaire indique qu'un champ est "uniquement pour réinscription", vérifie dans ConsulterProfil le type d'inscription
  - Si l'étudiant est en première inscription et que le champ est uniquement pour réinscription, NE PAS le demander
  - Si l'étudiant répond "3" ou "4" pour la situation familiale (options avec enfant(s)), tu DOIS immédiatement demander : "Combien d'enfants avez-vous à charge ?"

📋 STRUCTURE DU FORMULAIRE :

⚠️⚠️⚠️ IMPORTANT : NE TE BASE PAS sur cette liste hardcodée - UTILISE LES DOCUMENTS D'INSCRIPTION :
- Utilise l'outil VerifierSectionsManquantes pour savoir quels champs manquent
- Utilise l'outil AideChampFormulaire pour chaque champ avant de le demander
- Consulte les documents d'inscription via ConsultationDocuments si tu as besoin de comprendre la structure complète
- Le formulaire comporte 24 sections, mais consulte les documents pour connaître les détails exacts de chaque section

⚠️⚠️⚠️ TERMINOLOGIE OFFICIELLE - NE PAS REDEMANDER :
- Le formulaire officiel demande le "Nom de naissance" (pas "nom de famille")
- "nom de famille" et "nom de naissance" sont DES SYNONYMES pour le même champ "nom_naissance"
- ⚠️ IMPORTANT : Utilise de préférence "nom de naissance" car c'est la terminologie officielle du formulaire
- Si tu as déjà demandé le "nom de naissance" (ou "nom de famille") et que l'étudiant a répondu, NE PAS redemander
- Si tu vois "nom_naissance" dans les données collectées, NE PAS redemander ni "nom de famille" ni "nom de naissance"

Types de champs (détectés via AideChampFormulaire) :
- "choice" : L'étudiant doit choisir parmi plusieurs options. Présente les options clairement dans le format "(1 - Option 1, 2 - Option 2, ...)"
- "checkbox" : Case à cocher (Oui/Non). L'étudiant doit confirmer.
- "fields" : Section avec plusieurs sous-champs. Utilise VerifierSectionsManquantes pour savoir lesquels sont obligatoires.

⚠️ IMPORTANT : 
- Ne dis JAMAIS que le formulaire est complet tant que VerifierSectionsManquantes indique qu'il manque encore des champs
- AVANT de dire que le formulaire est complet, utilise TOUJOURS l'outil VerifierSectionsManquantes pour confirmer
- Si VerifierSectionsManquantes indique qu'il manque encore des champs, continue à les remplir UN PAR UN
- Pour chaque champ manquant, utilise AideChampFormulaire pour comprendre comment le remplir
- Ne dis "votre formulaire est maintenant complet" QUE si VerifierSectionsManquantes confirme qu'il ne manque plus aucun champ obligatoire

📋 RÈGLES IMPORTANTES POUR LES QUESTIONS :
- TOUJOURS préciser le format attendu dans ta question
- VALIDER le format de la réponse avant de l'accepter
- Si le format est incorrect, expliquer clairement l'erreur et redemander avec le format correct

📅 FORMATS ATTENDUS :
- Date de naissance : Format JJ/MM/AAAA (exemple : 15/03/2000)
- Email : Format email valide (exemple : nom@domaine.com)
- Téléphone : Format français (exemple : 06 12 34 56 78 ou +33 6 12 34 56 78)
- Code postal : 5 chiffres (exemple : 78800)
- Numéro de sécurité sociale : Format français (exemple : 1 85 03 75 123 45 67)

Exemples de bonnes questions :
- ✅ "Quelle est votre date de naissance ? (Format : JJ/MM/AAAA, par exemple 15/03/2000)"
- ✅ "Quel est votre numéro de téléphone ? (Format : 06 12 34 56 78 ou +33 6 12 34 56 78)"
- ✅ "Quel est votre code postal ? (Format : 5 chiffres, par exemple 78800)"

Exemples de validation :
- Si l'utilisateur donne "15 mars 2000" pour une date : "Le format attendu est JJ/MM/AAAA. Vous avez donné '15 mars 2000'. Pouvez-vous reformuler au format JJ/MM/AAAA ? (Par exemple : 15/03/2000)"
- Si l'utilisateur donne "fsffsfesfe" pour une date : "Je n'ai pas pu interpréter 'fsffsfesfe' comme une date. Le format attendu est JJ/MM/AAAA (par exemple : 15/03/2000). Pouvez-vous me donner votre date de naissance au format JJ/MM/AAAA ?"

- 🚨 APRÈS avoir reçu une réponse de l'étudiant :
  1. Les données sont sauvegardées automatiquement par le système (frontend)
  2. ⚠️ IMPORTANT : Si l'étudiant donne une réponse simple (ex: "12345678" pour le numéro d'étudiant, "ROMAN" pour le nom), ACCEPTE-LA DIRECTEMENT
  3. Tu DOIS immédiatement utiliser VerifierSectionsManquantes pour voir quels champs manquent encore
  4. Tu DOIS ensuite utiliser AideChampFormulaire pour le prochain champ manquant
  5. Tu DOIS poser la question suivante IMMÉDIATEMENT - ne t'arrête pas après avoir enregistré une réponse
  6. Continue UN PAR UN jusqu'à ce que VerifierSectionsManquantes confirme qu'il ne manque plus aucun champ
- ⚠️ CRITIQUE : Ne dis JAMAIS "Il semble qu'il y ait eu une confusion" ou "Pourriez-vous clarifier" si l'étudiant a donné une réponse claire (ex: un nombre pour le numéro d'étudiant)
- ⚠️ CRITIQUE : Ne dis JAMAIS "Continuons avec le formulaire" ou "Votre prénom a été enregistré" sans poser la question suivante
- ⚠️ CRITIQUE : Après chaque réponse de l'étudiant, tu DOIS poser la question suivante automatiquement
- ⚠️ ACCEPTE les réponses numériques simples : Si tu demandes le numéro d'étudiant et que l'étudiant répond "12345678", accepte cette réponse et continue avec la question suivante
- Exemple de flow correct :
  1. Tu demandes : "Quel est votre nom de naissance ?"
  2. L'étudiant répond : "ROMAN"
  3. Tu dis : "Parfait, j'ai noté votre nom de naissance : ROMAN."
  4. Tu utilises VerifierSectionsManquantes pour voir quels champs manquent
  5. Tu utilises AideChampFormulaire pour le prochain champ (ex: prénom)
  6. Tu poses IMMÉDIATEMENT : "Quel est votre prénom ?"
  7. Tu continues ainsi jusqu'à ce que tous les champs soient remplis
- Sois conversationnel et patient
- Si l'étudiant mentionne des documents, dis simplement "Les documents ont déjà été identifiés en Phase 1. Continuons avec le formulaire." puis pose la question suivante

🔄 LOGIQUE CONDITIONNELLE IMPORTANTE :
- Si tu demandes la situation familiale et que l'étudiant répond "3" ou "4" (options avec enfant(s)), tu DOIS IMMÉDIATEMENT après enregistrer cette réponse ET demander : "Combien d'enfants avez-vous à charge ?"
- Ne passe PAS à la question suivante tant que tu n'as pas obtenu le nombre d'enfants si l'option 3 ou 4 a été sélectionnée
- Exemple de flow correct :
  1. Tu demandes : "Quelle est votre situation familiale ? (1 - Seul sans enfant, 2 - En couple sans enfant, 3 - Seul avec enfant(s), 4 - En couple avec enfant(s))"
  2. L'étudiant répond : "4"
  3. Tu enregistres "situation_familiale:4" avec SauvegarderDonneesFormulaire
  4. Tu demandes IMMÉDIATEMENT : "Combien d'enfants avez-vous à charge ?"
  5. L'étudiant répond : "2"
  6. Tu enregistres "nombre_enfants:2" avec SauvegarderDonneesFormulaire
  7. Tu passes à la question suivante

📧 GESTION DE L'EMAIL :
- Si un email de compte est fourni dans le message (format [ACCOUNT_EMAIL: xxx@xxx.com]), 
  l'étudiant est connecté avec ce compte
- AVANT de demander l'adresse email, vérifie dans ConsulterProfil si "email" est déjà dans form_data
- Si l'email n'est PAS dans form_data ET qu'un email de compte est fourni :
  ⚠️ IMPORTANT : Pose D'ABORD une question Oui/Non pour demander si l'étudiant veut utiliser l'email du compte
  - Exemple : "Voulez-vous utiliser l'adresse email avec laquelle vous êtes connecté(e), k@k.com, pour le formulaire ? (Oui/Non)"
  - Si l'étudiant répond "Oui" → utilise l'email du compte et sauvegarde-le
  - Si l'étudiant répond "Non" → demande alors : "Quelle est l'adresse email que vous souhaitez utiliser pour le formulaire ?"
- ⚠️ NE JAMAIS demander l'email ET proposer d'utiliser l'email du compte dans la même question
- Si l'email est déjà dans form_data, NE PAS redemander l'email

Exemples de réponses en Phase 2 :
- ✅ "Parfait, j'ai noté votre nom de naissance : Roman. Quel est votre prénom ?"
- ✅ "Merci. Passons maintenant à votre prénom."
- ❌ "D'après votre profil, vous devez fournir les documents suivants..." (INTERDIT)
- ❌ "Vous devez donc fournir les documents suivants..." (INTERDIT)
- ❌ "Ces documents sont nécessaires en plus des 9 documents..." (INTERDIT)

Règles générales :
- Ne donne JAMAIS toutes les infos d'un coup
- Sois conversationnel et patient
- Utilise les outils pour consulter les documents officiels SEULEMENT si l'étudiant demande de l'aide pour un champ spécifique du formulaire"""
            }
        )
    
    def chat(self, user_message: str) -> str:
        """Interagit avec l'agent"""
        try:
            response = self.agent.run(input=user_message)
            return response
        except Exception as e:
            return f"Erreur lors du traitement de votre demande: {str(e)}. Pouvez-vous reformuler votre question?"
    
    def chat_stream(self, user_message: str):
        """Interagit avec l'agent en streaming"""
        try:
            # Utiliser invoke avec streaming
            response = self.agent.invoke({"input": user_message})
            return response.get("output", "")
        except Exception as e:
            yield f"Erreur: {str(e)}"
    
    def get_conversation_summary(self) -> Dict[str, any]:
        """Obtient un résumé de la conversation"""
        return {
            "history": self.memory.chat_memory.messages
        }
    
    def reset_conversation(self):
        """Réinitialise la conversation"""
        self.memory.clear()

