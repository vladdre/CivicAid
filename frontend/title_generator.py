"""
Generator de titluri pentru conversații bazat pe mesajul user-ului.
Generează un rezumat scurt folosind OpenAI API.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()


def generate_conversation_title(user_message: str) -> str:
    """
    Generează un titlu scurt pentru conversație bazat pe mesajul user-ului.
    
    Args:
        user_message: Mesajul trimis de user
        
    Returns:
        Titlu scurt (max 50 caractere) sau titlu default dacă nu se poate genera
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        # Dacă nu există API key, returnează primele 50 de caractere din mesaj
        return user_message[:50] + "..." if len(user_message) > 50 else user_message
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=api_key
        )
        
        prompt = f"""Generează un titlu foarte scurt (maximum 50 caractere) pentru o conversație bazat pe următorul mesaj al utilizatorului.

Mesaj utilizator: {user_message}

Cerințe:
- Titlul trebuie să fie foarte scurt și concis (max 50 caractere)
- Trebuie să reflecte esența întrebării sau subiectului
- Folosește limba română
- Nu include ghilimele sau caractere speciale
- Dacă mesajul este prea scurt sau neclar, folosește primele cuvinte relevante

Titlu:"""
        
        response = llm.invoke(prompt)
        title = response.content.strip()
        
        # Elimină ghilimele dacă există
        title = title.strip('"\'')
        
        # Limitează la 50 caractere
        if len(title) > 50:
            title = title[:47] + "..."
        
        return title if title else user_message[:50]
        
    except Exception as e:
        print(f"Eroare la generarea titlului: {e}")
        # Fallback: returnează primele 50 caractere din mesaj
        return user_message[:50] + "..." if len(user_message) > 50 else user_message

