"""
Application principale pour l'agent d'inscription Sciences Po Aix
"""
import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import json
import uuid
from dotenv import load_dotenv

from document_extractor import DocumentExtractor
from rag_system import RAGSystem
from inscription_agent import InscriptionAgent
from document_validator import DocumentValidator
from form_progress import FormProgressManager
from student_profile import ProfileManager, StudentProfile
from export_utils import format_documents_for_csv, format_documents_for_email
from user_account import AccountManager

# Charger les variables d'environnement
load_dotenv()

from contextlib import asynccontextmanager

# Configuration
DOCUMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(DOCUMENTS_DIR, "templates")
STATIC_DIR = os.path.join(DOCUMENTS_DIR, "static")

# Créer les répertoires si nécessaire
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Variables globales pour le système
rag_system = None
agent = None
extractor = None
progress_manager = FormProgressManager()
profile_manager = ProfileManager()
account_manager = AccountManager()


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[dict]] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    global rag_system, agent, extractor
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("⚠️  ATTENTION: OPENAI_API_KEY non définie. Le système ne fonctionnera pas correctement.")
        print("   Créez un fichier .env avec: OPENAI_API_KEY=votre_cle")
        yield
        return
    
    try:
        # Initialiser l'extracteur
        extractor = DocumentExtractor(documents_dir=DOCUMENTS_DIR)
        
        # Extraire tous les documents
        print("📄 Extraction des documents...")
        documents = extractor.extract_all_documents()
        print(f"✅ {len(documents)} documents extraits")
        
        # Initialiser le système RAG
        print("🧠 Initialisation du système RAG...")
        rag_system = RAGSystem(openai_api_key=openai_api_key)
        rag_system.initialize_vectorstore(documents)
        print("✅ Système RAG initialisé")
        
        # Initialiser l'agent
        print("🤖 Initialisation de l'agent...")
        agent = InscriptionAgent(rag_system=rag_system, openai_api_key=openai_api_key, profile_manager=profile_manager)
        print("✅ Agent initialisé")
        
        print("\n🎉 Système prêt à l'emploi!")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {str(e)}")
    
    yield
    
    # Shutdown (si nécessaire)
    pass

app = FastAPI(title="Agent d'inscription Sciences Po Aix", version="1.0.0", lifespan=lifespan)

# Supprimer l'ancien 

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Page d'accueil"""
    return templates.TemplateResponse("index.html", {"request": request})


async def generate_stream(agent, message: str):
    """Génère une réponse en streaming"""
    try:
        # Pour l'instant, on simule le streaming en divisant la réponse
        # TODO: Implémenter le vrai streaming avec LangChain
        response = agent.chat(message)
        
        # Diviser la réponse en chunks pour simuler le streaming
        words = response.split()
        chunk_size = 3  # 3 mots par chunk
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size]) + " "
            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
        
        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
    except Exception as e:
        error_msg = f"Erreur: {str(e)}"
        yield f"data: {json.dumps({'content': error_msg, 'done': True, 'error': True})}\n\n"


@app.post("/api/chat")
async def chat_endpoint(chat_message: ChatMessage):
    """Endpoint pour le chat avec l'agent (streaming)"""
    if not agent:
        raise HTTPException(status_code=503, detail="Le système n'est pas encore initialisé")
    
    # Ajouter le session_id au message pour que l'agent puisse consulter le profil
    message_with_context = chat_message.message
    if chat_message.session_id:
        message_with_context = f"[SESSION_ID: {chat_message.session_id}] {chat_message.message}"
    
    return StreamingResponse(
        generate_stream(agent, message_with_context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/chat-sync", response_model=ChatResponse)
async def chat_endpoint_sync(chat_message: ChatMessage):
    """Endpoint pour le chat avec l'agent (synchronisé, pour compatibilité)"""
    if not agent:
        raise HTTPException(status_code=503, detail="Le système n'est pas encore initialisé")
    
    try:
        response = agent.chat(chat_message.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.get("/api/codes")
async def get_codes(category: Optional[str] = None):
    """Obtenir les codes d'inscription"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="Le système n'est pas encore initialisé")
    
    try:
        result = rag_system.get_codes(category)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.get("/api/documents")
async def get_required_documents():
    """Obtenir la liste des pièces à fournir"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="Le système n'est pas encore initialisé")
    
    try:
        result = rag_system.check_required_documents()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/api/help-field")
async def help_with_field(field_name: str):
    """Aide pour un champ spécifique"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="Le système n'est pas encore initialisé")
    
    try:
        result = rag_system.help_with_form_field(field_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/api/reset")
async def reset_conversation():
    """Réinitialise la conversation"""
    if not agent:
        raise HTTPException(status_code=503, detail="Le système n'est pas encore initialisé")
    
    agent.reset_conversation()
    return {"message": "Conversation réinitialisée"}


@app.post("/api/validate-documents")
async def validate_documents():
    """Valide tous les documents dans le répertoire"""
    try:
        validator = DocumentValidator()
        results = validator.validate_all_documents(DOCUMENTS_DIR)
        report = validator.get_validation_report(results)
        
        return {
            "valid": results["valid"],
            "summary": results["summary"],
            "documents": results["documents"],
            "missing": results["missing"],
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# Endpoints pour le système de profils et formulaire
@app.post("/api/profile/start")
async def start_profile():
    """Démarre un nouveau profil étudiant (Phase 1)"""
    session_id = str(uuid.uuid4())
    profile = profile_manager.create_profile(session_id)
    return {
        "session_id": session_id,
        "phase": profile.phase,
        "message": "Profil créé. Commencez par répondre aux questions pour déterminer vos documents nécessaires."
    }


@app.get("/api/profile/{session_id}")
async def get_profile(session_id: str):
    """Récupère le profil d'un étudiant"""
    profile = profile_manager.load_profile(session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    return profile.to_dict()


@app.post("/api/profile/{session_id}/update")
async def update_profile(session_id: str, request: Request):
    """Met à jour le profil avec les informations collectées"""
    profile = profile_manager.load_profile(session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    
    data = await request.json()
    
    # Mettre à jour les champs
    if "inscription_type" in data:
        profile.inscription_type = data["inscription_type"]
    if "is_boursier" in data:
        profile.is_boursier = data["is_boursier"]
    if "is_mineur" in data:
        profile.is_mineur = data["is_mineur"]
    if "inscrit_autre_etablissement" in data:
        profile.inscrit_autre_etablissement = data["inscrit_autre_etablissement"]
    if "has_jdc" in data:
        profile.has_jdc = data["has_jdc"]
    
    # Recalculer les documents nécessaires
    profile.calculate_required_documents()
    
    # Vérifier si la phase 1 est complète
    if profile.is_phase1_complete() and profile.phase == "collecte_info":
        profile.move_to_phase2()
    
    profile_manager.save_profile(profile)
    
    return {
        "profile": profile.to_dict(),
        "phase1_complete": profile.is_phase1_complete(),
        "required_documents": profile.required_documents
    }


@app.post("/api/profile/{session_id}/phase2")
async def start_phase2(session_id: str):
    """Passe à la phase 2 (remplissage du formulaire)"""
    profile = profile_manager.load_profile(session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    
    if not profile.is_phase1_complete():
        raise HTTPException(status_code=400, detail="La phase 1 n'est pas complète")
    
    profile.move_to_phase2()
    profile_manager.save_profile(profile)
    
    return {
        "message": "Phase 2 démarrée. Vous pouvez maintenant remplir le formulaire.",
        "profile": profile.to_dict()
    }


@app.post("/api/profile/{session_id}/form-data")
async def update_form_data(session_id: str, request: Request):
    """Met à jour les données du formulaire (Phase 2)"""
    profile = profile_manager.load_profile(session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    
    if profile.phase != "remplissage_formulaire":
        raise HTTPException(status_code=400, detail="Vous devez d'abord compléter la phase 1")
    
    data = await request.json()
    profile.form_data.update(data.get("form_data", {}))
    profile.current_step = data.get("current_step", profile.current_step)
    
    if "completed_steps" in data:
        profile.completed_steps = data["completed_steps"]
    
    profile_manager.save_profile(profile)
    
    return {"message": "Données du formulaire mises à jour", "profile": profile.to_dict()}


# Endpoints pour les comptes utilisateurs
@app.post("/api/account/create")
async def create_account(request: Request):
    """Crée un nouveau compte utilisateur"""
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email requis")
    
    try:
        account = account_manager.create_account(email, password)
        return {"message": "Compte créé", "email": account.email}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/account/login")
async def login(request: Request):
    """Connecte un utilisateur"""
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email requis")
    
    account = account_manager.authenticate(email, password) if password else account_manager.get_account(email)
    
    if not account:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    return {"message": "Connecté", "email": account.email, "profiles": account.profiles}


@app.post("/api/account/{email}/save-profile")
async def save_profile_to_account(email: str, request: Request):
    """Sauvegarde un profil dans un compte utilisateur"""
    data = await request.json()
    session_id = data.get("session_id")
    profile_data = data.get("profile_data")
    
    if not session_id or not profile_data:
        raise HTTPException(status_code=400, detail="session_id et profile_data requis")
    
    account = account_manager.get_account(email)
    if not account:
        raise HTTPException(status_code=404, detail="Compte non trouvé")
    
    account.save_profile(session_id, profile_data)
    account_manager.save_account(account)
    
    return {"message": "Profil sauvegardé", "session_id": session_id}


@app.get("/api/profile/{session_id}/export")
async def export_documents(session_id: str, format: str = "csv"):
    """Exporte la liste des documents dans différents formats"""
    profile = profile_manager.load_profile(session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    
    if not profile.required_documents:
        raise HTTPException(status_code=400, detail="Aucun document à exporter")
    
    student_info = {
        "inscription_type": profile.inscription_type,
        "nom": profile.form_data.get("nom", ""),
        "prenom": profile.form_data.get("prenom", "")
    }
    
    # Normaliser le format (enlever les espaces, mettre en minuscules)
    format = format.strip().lower() if format else "csv"
    
    if format == "csv":
        try:
            csv_content = format_documents_for_csv(profile.required_documents, student_info)
            return Response(
                content=csv_content.encode('utf-8-sig'),  # UTF-8 avec BOM pour Excel
                media_type="text/csv;charset=utf-8",
                headers={
                    "Content-Disposition": "attachment; filename=documents-a-fournir.csv",
                    "Content-Type": "text/csv;charset=utf-8"
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du CSV: {str(e)}")
    elif format == "email":
        email_data = format_documents_for_email(profile.required_documents, student_info)
        return email_data
    else:
        raise HTTPException(status_code=400, detail=f"Format non supporté: '{format}'. Utilisez 'csv' ou 'email'")


# Endpoints pour le formulaire interactif (compatibilité)
@app.post("/api/form/start")
async def start_form():
    """Démarre un nouveau formulaire et retourne un session_id"""
    session_id = str(uuid.uuid4())
    progress_manager.save_progress(session_id, {}, "start")
    return {"session_id": session_id}


@app.get("/api/form/progress/{session_id}")
async def get_form_progress(session_id: str):
    """Récupère la progression du formulaire"""
    progress = progress_manager.load_progress(session_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    return progress


@app.post("/api/form/save")
async def save_form_progress(request: Request):
    """Sauvegarde la progression du formulaire"""
    data = await request.json()
    session_id = data.get("session_id")
    form_data = data.get("form_data", {})
    current_step = data.get("current_step", "start")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id requis")
    
    success = progress_manager.save_progress(session_id, form_data, current_step)
    if success:
        return {"message": "Progression sauvegardée", "session_id": session_id}
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")


@app.delete("/api/form/progress/{session_id}")
async def delete_form_progress(session_id: str):
    """Supprime la progression du formulaire"""
    success = progress_manager.delete_progress(session_id)
    if success:
        return {"message": "Progression supprimée"}
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

