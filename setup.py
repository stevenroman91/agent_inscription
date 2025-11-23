"""
Script de configuration initiale pour l'agent d'inscription
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def check_setup():
    """Vérifie que tout est configuré correctement"""
    print("🔍 Vérification de la configuration...")
    
    # Vérifier les fichiers de documents
    required_docs = [
        "Dossier-dinscription-administrative-2025-2026 (2).docx",
        "Pieces-a-fournir-2025-2026.pdf",
        "Annexes-inscriptions-administratives-2025-2026.pdf"
    ]
    
    missing_docs = []
    for doc in required_docs:
        if not Path(doc).exists():
            missing_docs.append(doc)
    
    if missing_docs:
        print("⚠️  Documents manquants:")
        for doc in missing_docs:
            print(f"   - {doc}")
    else:
        print("✅ Tous les documents requis sont présents")
    
    # Vérifier la clé API
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY non définie dans le fichier .env")
        print("   Créez un fichier .env avec: OPENAI_API_KEY=votre_cle")
    else:
        print("✅ Clé API OpenAI configurée")
    
    # Vérifier les dépendances
    try:
        import fastapi
        import langchain
        import chromadb
        print("✅ Dépendances principales installées")
    except ImportError as e:
        print(f"❌ Dépendances manquantes: {e}")
        print("   Installez-les avec: pip install -r requirements.txt")
    
    print("\n" + "="*60)
    if not missing_docs and api_key:
        print("✅ Configuration complète! Vous pouvez lancer: python main.py")
    else:
        print("⚠️  Veuillez corriger les problèmes ci-dessus avant de continuer")
    print("="*60)

if __name__ == "__main__":
    check_setup()

