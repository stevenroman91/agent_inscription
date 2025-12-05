"""
Système RAG pour les documents d'inscription Sciences Po Aix
"""
import os
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from document_extractor import DocumentExtractor


class RAGSystem:
    """Système RAG pour gérer les documents d'inscription"""
    
    def __init__(self, openai_api_key: str, persist_directory: str = "./chroma_db"):
        self.openai_api_key = openai_api_key
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            api_key=openai_api_key
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vectorstore = None
        self.qa_chain = None
    
    def initialize_vectorstore(self, documents: List[Dict[str, any]]):
        """Initialise le vector store avec les documents extraits"""
        texts = []
        metadatas = []
        
        for doc in documents:
            if doc["type"] in ["pdf", "docx"]:
                # Diviser le texte en chunks
                chunks = self.text_splitter.split_text(doc["text"])
                
                for i, chunk in enumerate(chunks):
                    texts.append(chunk)
                    metadatas.append({
                        "source": doc["file_name"],
                        "type": doc["type"],
                        "chunk_index": i
                    })
        
        if texts:
            # Créer ou charger le vector store
            self.vectorstore = Chroma.from_texts(
                texts=texts,
                metadatas=metadatas,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # Créer la chaîne QA
            self._create_qa_chain()
    
    def _create_qa_chain(self):
        """Crée la chaîne de question-réponse"""
        prompt_template = """Tu es un assistant spécialisé dans l'aide aux inscriptions à Sciences Po Aix. 
Tu as accès à tous les documents officiels d'inscription et tu dois aider les étudiants à :
1. Comprendre les questions du dossier d'inscription
2. Trouver les codes appropriés à utiliser
3. Vérifier que toutes les pièces nécessaires sont fournies
4. Éviter les erreurs courantes

Utilise les informations suivantes pour répondre à la question de l'étudiant. Si tu ne trouves pas l'information dans les documents, dis-le clairement.

Contexte:
{context}

Question: {question}

Réponse détaillée et utile:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
    
    def query(self, question: str) -> Dict[str, any]:
        """Pose une question au système RAG"""
        if not self.qa_chain:
            raise Exception("Le système RAG n'est pas initialisé. Appelez d'abord initialize_vectorstore()")
        
        result = self.qa_chain({"query": question})
        
        return {
            "answer": result["result"],
            "sources": [
                {
                    "source": doc.metadata.get("source", "Unknown"),
                    "content": doc.page_content[:200] + "..."
                }
                for doc in result.get("source_documents", [])
            ]
        }
    
    def get_codes(self, category: Optional[str] = None) -> Dict[str, any]:
        """Récupère les codes d'inscription (depuis les annexes)"""
        if category:
            question = f"Quels sont les codes pour {category} dans les annexes d'inscription?"
        else:
            question = "Liste tous les codes disponibles dans les annexes d'inscription administrative avec leurs descriptions"
        
        return self.query(question)
    
    def check_required_documents(self) -> Dict[str, any]:
        """Vérifie la liste des pièces à fournir"""
        question = "Quelle est la liste complète des pièces à fournir pour l'inscription administrative à Sciences Po Aix?"
        return self.query(question)
    
    def help_with_form_field(self, field_name: str) -> Dict[str, any]:
        """Aide à remplir un champ spécifique du formulaire"""
        # Mapper les noms de champs internes vers les noms utilisés dans le formulaire
        field_mapping = {
            "numero_etudiant": "N° Etudiant",
            "numero_ines": "N° INES",
            "nom_naissance": "Nom de naissance",
            "prenom_1": "Prénom",
            "date_naissance": "Date de naissance",
            "situation_familiale": "Situation familiale",
            "departement_naissance": "Département de naissance",
            "pays_naissance": "Pays de naissance",
            "nationalite": "Nationalité",
            "premiere_inscription_universite_etablissement": "Etablissement première inscription université",
            "bac_serie": "Série baccalauréat",
            "bac_departement": "Département baccalauréat",
            "csp_etudiant_code": "Code CSP étudiant",
            "csp_parent_1": "Code CSP parent 1",
            "csp_parent_2": "Code CSP parent 2",
            "dernier_diplome_code": "Code diplôme",
            "dernier_diplome_etablissement": "Etablissement dernier diplôme",
            "diplome_postule_code_cpge": "Code CPGE"
        }
        
        field_display_name = field_mapping.get(field_name, field_name)
        
        # Vérifier si le champ nécessite un code d'annexe
        try:
            from field_detection import requires_code, get_annexe_number
            needs_code = requires_code(field_name)
            annexe_num = get_annexe_number(field_name) if needs_code else None
        except:
            needs_code = "annexe" in field_name.lower() or "code" in field_name.lower()
            annexe_num = None
        
        question = f"""Dans le dossier d'inscription administrative, pour le champ "{field_display_name}" (ou "{field_name}") :
1. Quel est le format exact attendu (nombre de caractères, type de données, etc.) ?
2. Où l'étudiant peut-il trouver cette information ?
3. Y a-t-il des conditions particulières (par exemple : uniquement pour réinscription, uniquement pour bacheliers, etc.) ?
4. Quelles sont les instructions spécifiques données dans le dossier d'inscription pour ce champ ?"""
        
        if needs_code and annexe_num:
            question += f"\n5. ⚠️ IMPORTANT : Ce champ nécessite un CODE depuis l'ANNEXE {annexe_num}. Quels sont les codes disponibles dans l'annexe {annexe_num} pour ce champ ? Liste les codes avec leurs descriptions pour aider l'étudiant à choisir."
        elif needs_code:
            question += f"\n5. ⚠️ IMPORTANT : Ce champ nécessite un CODE depuis une ANNEXE. Quelle annexe contient les codes pour ce champ ? Liste les codes disponibles avec leurs descriptions."
        
        question += "\n\nDonne-moi toutes les informations utiles du dossier d'inscription pour aider l'étudiant à remplir ce champ correctement."
        
        return self.query(question)

