#!/bin/bash

# Script de démarrage pour l'agent d'inscription Sciences Po Aix

echo "🎓 Démarrage de l'agent d'inscription Sciences Po Aix"
echo ""

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Vérifier que les dépendances sont installées
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installation des dépendances..."
    pip3 install -r requirements.txt
fi

# Vérifier la configuration
echo "🔍 Vérification de la configuration..."
python3 setup.py

echo ""
echo "🚀 Démarrage du serveur..."
echo "   L'application sera accessible sur: http://localhost:8000"
echo "   Appuyez sur Ctrl+C pour arrêter"
echo ""

python3 main.py

