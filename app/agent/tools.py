"""
Definiții tool-uri pentru OpenAI Functions Agent.
"""

from typing import Dict, Any
from app.core.query_processor import process_query
from app.tools.sql import query_institutions


def consult_legislation(user_message: str, conversation_history: list = None) -> str:
    """
    Consultă legislația română pentru a găsi informații relevante.
    
    Args:
        user_message: Mesajul utilizatorului
        conversation_history: Istoricul conversației (opțional)
        
    Returns:
        Rezumat sintetizat al informațiilor găsite în legislație
    """
    try:
        result = process_query(user_message, conversation_history=conversation_history, verbose=False)
        return result
    except Exception as e:
        return f"❌ Eroare la consultarea legislației: {str(e)}"


def get_institution_address(user_message: str, conversation_history: list = None) -> str:
    """
    Găsește adrese și informații despre instituții publice.
    
    Args:
        user_message: Mesajul utilizatorului
        conversation_history: Istoricul conversației (opțional)
        
    Returns:
        Lista de instituții cu adrese, program și contact
    """
    try:
        result = query_institutions(
            natural_language_query=user_message,
            vector_store_output=None,
            conversation_history=conversation_history
        )
        return result if result else "Nu s-au găsit instituții relevante."
    except Exception as e:
        return f"❌ Eroare la căutarea instituțiilor: {str(e)}"


# Definiții tool-uri pentru OpenAI Functions
TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "consult_legislation",
            "description": "Consultă legislația română pentru a găsi informații despre legi, articole, reglementări și drepturi. Folosește acest tool când utilizatorul întreabă despre legi, drepturi legale, proceduri legale, sau orice aspect juridic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "Mesajul utilizatorului care conține întrebarea despre legislație"
                    }
                },
                "required": ["user_message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_institution_address",
            "description": "Găsește adrese, program de lucru și informații de contact pentru instituții publice românești (ex: case de pensii, primării, instituții publice). Folosește acest tool când utilizatorul întreabă despre unde să meargă, adrese, program de lucru, sau contact pentru instituții.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "Mesajul utilizatorului care conține întrebarea despre instituții, adrese sau locații"
                    }
                },
                "required": ["user_message"]
            }
        }
    }
]


# Mapare funcții pentru execuție
TOOLS_MAP = {
    "consult_legislation": consult_legislation,
    "get_institution_address": get_institution_address
}

