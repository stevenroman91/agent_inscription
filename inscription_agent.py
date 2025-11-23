"""
Agent intelligent pour guider les étudiants dans le processus d'inscription
"""
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from rag_system import RAGSystem
from form_sections import FORM_SECTIONS, get_missing_sections, is_form_complete, get_section_by_field


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
            description="Utilise cet outil pour consulter les documents officiels d'inscription (dossier, pièces à fournir, codes, annexes). Utilise-le quand tu as besoin d'informations précises sur le processus d'inscription."
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
            description="Utilise cet outil quand un étudiant demande de l'aide pour remplir un champ spécifique du formulaire d'inscription."
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
            info += f"- Boursier: {profile.is_boursier if profile.is_boursier is not None else 'Non défini'}\n"
            info += f"- Mineur: {profile.is_mineur if profile.is_mineur is not None else 'Non défini'}\n"
            info += f"- Inscrit ailleurs: {profile.inscrit_autre_etablissement if profile.inscrit_autre_etablissement is not None else 'Non défini'}\n"
            info += f"- JDC fournie: {profile.has_jdc if profile.has_jdc is not None else 'Non défini'}\n"
            info += f"- Phase actuelle: {profile.phase}\n"
            if profile.required_documents:
                info += f"- Documents requis: {len(profile.required_documents)} documents identifiés\n"
            
            # Ajouter les données du formulaire si disponibles
            if profile.form_data:
                info += f"\nDONNÉES DU FORMULAIRE DÉJÀ COLLECTÉES:\n"
                for key, value in profile.form_data.items():
                    if value:  # Ne montrer que les champs remplis
                        info += f"- {key}: {value}\n"
                if not any(profile.form_data.values()):
                    info += "- Aucune donnée collectée pour le moment\n"
            else:
                info += f"\nDONNÉES DU FORMULAIRE: Aucune donnée collectée pour le moment\n"
            
            return info
        
        profile_tool = Tool(
            name="ConsulterProfil",
            func=get_profile_info_wrapper,
            description="⚠️ IMPORTANT: Utilise CET OUTIL EN PREMIER avant de répondre. Passe le session_id (qui est dans le message entre [SESSION_ID: ...]). Il te donne toutes les informations déjà collectées sur l'étudiant, y compris la phase actuelle ET les données du formulaire déjà remplies. Si la phase est 'remplissage_formulaire', tu es en Phase 2 et tu dois UNIQUEMENT aider à remplir le formulaire, SANS mentionner les documents. NE JAMAIS redemander une information déjà présente dans 'DONNÉES DU FORMULAIRE DÉJÀ COLLECTÉES'."
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
            description="⚠️ Utilise cet outil APRÈS avoir collecté une réponse de l'étudiant pour un champ du formulaire. Format: 'nom:Roman' ou 'prenom:Steven' ou 'email:test@example.com'. Les données seront sauvegardées automatiquement. Utilise cet outil après chaque réponse de l'étudiant pour un champ du formulaire."
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
            
            info = f"📋 SECTIONS MANQUANTES ({len(missing)} sur 24 sections obligatoires):\n"
            for section in missing[:10]:  # Limiter à 10 pour ne pas surcharger
                info += f"- Section {section['number']}: {section['name']} (champ: {section['field']}, format: {section['format']})\n"
            if len(missing) > 10:
                info += f"... et {len(missing) - 10} autres sections\n"
            info += f"\nTu dois remplir TOUTES ces sections avant de dire que le formulaire est complet."
            return info
        
        check_sections_tool = Tool(
            name="VerifierSectionsManquantes",
            func=check_missing_sections_wrapper,
            description="⚠️ IMPORTANT: Utilise cet outil régulièrement pour vérifier quelles sections du formulaire sont encore manquantes. Passe le session_id (qui est dans le message entre [SESSION_ID: ...]). Il te dit combien de sections manquent et lesquelles. Ne dis JAMAIS que le formulaire est complet tant que cet outil ne confirme pas que toutes les sections sont remplies."
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

⚠️⚠️⚠️ RÈGLE CRITIQUE ABSOLUE : AVANT de répondre :
1. Vérifie si le message contient [ACCOUNT_EMAIL: xxx@xxx.com] - cela signifie que l'étudiant est connecté avec ce compte
2. Utilise TOUJOURS l'outil ConsulterProfil pour connaître la phase actuelle de l'étudiant ET les données déjà collectées
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
- AVANT de poser une question, utilise TOUJOURS l'outil ConsulterProfil pour vérifier les données déjà collectées
- NE JAMAIS redemander une information déjà présente dans "DONNÉES DU FORMULAIRE DÉJÀ COLLECTÉES"
- Le formulaire d'inscription comporte 24 SECTIONS OBLIGATOIRES à remplir
- Tu dois remplir TOUTES les sections avant de dire que le formulaire est complet
- Concentre-toi UNIQUEMENT sur le remplissage du formulaire
- Pose des questions UNE PAR UNE pour chaque section MANQUANTE dans l'ordre (section 1, puis 2, puis 3, etc.)

📝 RÈGLES POUR LES DIFFÉRENTS TYPES DE CHAMPS :
- Pour les champs de type "choice" : Présente TOUJOURS toutes les options disponibles dans le format EXACT : "(1 - Option 1, 2 - Option 2, 3 - Option 3, 4 - Option 4)"
  Exemple : "Quelle est votre situation familiale ? (1 - Seul sans enfant, 2 - En couple sans enfant, 3 - Seul avec enfant(s), 4 - En couple avec enfant(s))"
  ⚠️ IMPORTANT : Utilise TOUJOURS ce format avec parenthèses et tirets pour que le frontend puisse détecter les choix multiples
- Pour les sections avec plusieurs champs ("fields") : Remplis TOUS les champs obligatoires de la section avant de passer à la suivante
  Exemple : Pour la section 2 (Etat civil), tu dois demander : nom, prénom 1, puis optionnellement prénom 2, prénom 3, etc.
- Pour les checkboxes : Demande une confirmation claire (Oui/Non)
  Exemple : "Certifiez-vous sur l'honneur l'exactitude des renseignements fournis ? (Oui/Non)"
- Pour les champs conditionnels : Ne les demande QUE si la condition est remplie
  ⚠️ CRITIQUE : Si l'étudiant répond "3" ou "4" pour la situation familiale (options avec enfant(s)), tu DOIS immédiatement demander : "Combien d'enfants avez-vous à charge ?"
  Exemple : Si l'étudiant choisit "4 - En couple avec enfant(s)" pour la situation familiale, demande IMMÉDIATEMENT après : "Combien d'enfants avez-vous à charge ?"

📋 LES 24 SECTIONS DU FORMULAIRE (avec types de champs) :

IMPORTANT : Certaines sections contiennent PLUSIEURS champs à remplir. Tu dois remplir TOUS les champs obligatoires d'une section avant de passer à la suivante.

Types de champs :
- "choice" : L'étudiant doit choisir parmi plusieurs options. Présente les options clairement.
- "checkbox" : Case à cocher (Oui/Non). L'étudiant doit confirmer.
- "fields" : Section avec plusieurs sous-champs. Remplis-les tous avant de passer à la section suivante.

1. Type d'inscription (choice: 1ère Inscription ou Réinscription)
2. Etat civil (plusieurs champs: nom, prénoms, N° étudiant, N° INES)
3. Date de naissance et sexe (date JJ/MM/AAAA + choice: M. ou F.)
4. Lieu de naissance (ville, département, pays avec codes)
5. Nationalité (code pays + checkbox réfugié politique)
6. Situation familiale (choice: 1, 2, 3 ou 4 + nombre d'enfants si applicable)
7. Handicap (info optionnelle)
8. Situation militaire (choice: 3, 4, 5, 6 ou 7)
9. Première inscription supérieur français (plusieurs champs: années, établissement)
10. Baccalauréat (plusieurs champs: année, série, mention, spécialités, établissement)
11. Adresses (adresse complète + choice type d'hébergement: 1 à 7)
12. CSP de l'étudiant (code + choice activité + choice quotité)
13. CSP des parents (code parent 1 + code parent 2)
14. Sportif de haut niveau (choice optionnel: National, Régional, Universitaire)
15. Aides financières (optionnel)
16. Échanges internationaux (choice Oui/Non + détails si Oui)
17. Dernier établissement fréquenté (année + établissement français ou étranger)
18. Situation 2025-2026 (choice: T, U, Q, R + établissement si applicable)
19. Dernier diplôme obtenu (code, libellé, année, établissement)
20. Inscrit autre établissement (choice Oui/Non + établissement si Oui)
21. Diplôme postulé principal (plusieurs champs: intitulé, spécialité, parcours, niveau, etc.)
22. Autre diplôme postulé (optionnel, plusieurs champs)
23. Informations complémentaires (pupilles nation, assurance, mineur - tous choice Oui/Non)
24. Certifications et signature (2 checkboxes obligatoires + date + lieu)

⚠️ IMPORTANT : 
- Ne dis JAMAIS que le formulaire est complet tant que tu n'as pas rempli TOUTES les 24 sections obligatoires
- AVANT de dire que le formulaire est complet, utilise TOUJOURS l'outil VerifierSectionsManquantes pour confirmer
- Si VerifierSectionsManquantes indique qu'il manque encore des sections, continue à les remplir dans l'ordre (section 1, puis 2, puis 3, etc.)
- Ne dis "votre formulaire est maintenant complet" QUE si VerifierSectionsManquantes confirme que toutes les sections sont remplies

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

- APRÈS avoir reçu une réponse de l'étudiant, utilise l'outil SauvegarderDonneesFormulaire pour enregistrer la réponse
- Exemple : Si l'étudiant dit "Roman" pour le nom, utilise SauvegarderDonneesFormulaire avec "nom:Roman"
- Sois conversationnel et patient
- Si l'étudiant mentionne des documents, dis simplement "Les documents ont déjà été identifiés en Phase 1. Continuons avec le formulaire."

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
- Si l'email n'est PAS dans form_data ET qu'un email de compte est fourni, propose D'ABORD d'utiliser l'email du compte connecté
- Exemple : "Je vois que vous êtes connecté avec test@example.com. Souhaitez-vous utiliser cette adresse email pour le formulaire, ou préférez-vous utiliser une autre adresse ?"
- Si l'étudiant accepte, utilise l'email du compte. Sinon, demande l'email qu'il souhaite utiliser
- Si l'email est déjà dans form_data, NE PAS redemander l'email

Exemples de réponses en Phase 2 :
- ✅ "Parfait, j'ai noté votre nom de famille : Roman. Quel est votre prénom ?"
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

