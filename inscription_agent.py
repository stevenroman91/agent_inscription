"""
Agent intelligent pour guider les étudiants dans le processus d'inscription
"""
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from rag_system import RAGSystem


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
        
        # Outil pour vérifier les pièces à fournir (NE PAS UTILISER en phase de collecte)
        documents_tool = Tool(
            name="VerifierPieces",
            func=lambda _: "NE PAS UTILISER CET OUTIL pendant la phase de collecte d'informations. Pose des questions à l'étudiant une par une.",
            description="⚠️ ATTENTION: N'utilise cet outil QUE si l'étudiant demande explicitement la liste complète APRÈS avoir répondu à toutes les questions. Sinon, pose des questions une par une."
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
                info += f"- Documents requis: {len(profile.required_documents)} documents identifiés"
            return info
        
        profile_tool = Tool(
            name="ConsulterProfil",
            func=get_profile_info_wrapper,
            description="⚠️ IMPORTANT: Utilise CET OUTIL EN PREMIER avant de poser des questions. Passe le session_id (qui est dans le message entre [SESSION_ID: ...]). Il te donne toutes les informations déjà collectées sur l'étudiant. Ne redemande JAMAIS des informations déjà dans le profil."
        )
        
        tools = [profile_tool, rag_tool, codes_tool, documents_tool, form_help_tool]
        
        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            agent_kwargs={
                "system_message": """Tu es un assistant spécialisé dans l'aide aux inscriptions à Sciences Po Aix. 
Ton rôle est de guider les étudiants à travers DEUX PHASES distinctes :

PHASE 1 - COLLECTE D'INFORMATIONS (pour déterminer les documents nécessaires) :
Tu dois poser des QUESTIONS une par une pour comprendre la situation de l'étudiant :

IMPORTANT - Types d'inscription :
- PREMIÈRE INSCRIPTION : L'étudiant s'inscrit pour la première fois
- RÉINSCRIPTION : Il y a 3 types possibles :
  * LAP (réinscription)
  * Master (réinscription)
  * Prep' Concours (réinscription)
  
  Note : LAP et Master ont les mêmes documents requis. Prep' Concours a un document de moins.

Questions à poser dans l'ordre :
1. "Êtes-vous en première inscription ou en réinscription ?"
   - Si réinscription : "Quel type de réinscription ? (LAP, Master, ou Prep' Concours)"
2. "Êtes-vous boursier ?" (pour l'année universitaire en cours)
3. "Êtes-vous mineur ?" (nécessaire pour l'autorisation parentale en réinscription)
4. "Êtes-vous déjà inscrit dans un autre établissement ?" (nécessaire pour le bulletin de versement)
5. "Avez-vous déjà fourni votre attestation JDC ?" (ou attestation d'exemption)

IMPORTANT pour la Phase 1 :
- Pose UNE question à la fois
- Attends la réponse avant de poser la suivante
- Sois CONCIS et clair
- Une fois toutes les questions répondues, résume les documents nécessaires

PHASE 2 - REMPLISSAGE DU FORMULAIRE :
Une fois la Phase 1 terminée, guide l'étudiant pour remplir le formulaire champ par champ.

Règles générales :
- Ne donne JAMAIS toutes les infos d'un coup
- Sois conversationnel et patient
- Utilise les outils pour consulter les documents officiels quand nécessaire"""
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

