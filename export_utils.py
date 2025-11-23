"""
Utilitaires pour l'export des documents
"""
from typing import List
from datetime import datetime
import csv
from io import StringIO


def format_documents_for_csv(documents: List[str], student_info: dict = None) -> str:
    """Formate les documents pour un export CSV"""
    output = StringIO()
    writer = csv.writer(output, delimiter=';', lineterminator='\n')
    
    # En-tête
    writer.writerow(['DOCUMENTS À FOURNIR - SCIENCES PO AIX'])
    writer.writerow([])
    
    # Informations étudiant
    if student_info:
        writer.writerow(['Étudiant:', f"{student_info.get('nom', '')} {student_info.get('prenom', '')}"])
        writer.writerow(['Type d\'inscription:', student_info.get('inscription_type', '')])
        writer.writerow([])
    
    # En-tête du tableau
    writer.writerow(['Numéro', 'Document'])
    writer.writerow([])
    
    # Liste des documents
    for i, doc in enumerate(documents, 1):
        writer.writerow([i, doc])
    
    writer.writerow([])
    writer.writerow(['Généré le', datetime.now().strftime('%d/%m/%Y')])
    writer.writerow(['Source', 'Agent d\'inscription Sciences Po Aix'])
    
    return output.getvalue()


def format_documents_for_email(documents: List[str], student_info: dict = None) -> dict:
    """Formate les documents pour un email"""
    subject = "Documents à fournir - Sciences Po Aix"
    
    body = "Bonjour,\n\n"
    body += "Voici la liste des documents à fournir pour mon inscription à Sciences Po Aix :\n\n"
    
    for i, doc in enumerate(documents, 1):
        body += f"{i}. {doc}\n"
    
    body += "\nCordialement"
    
    return {
        "subject": subject,
        "body": body
    }

