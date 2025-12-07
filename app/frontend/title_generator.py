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
        
        prompt = f"""Generează un titlu scurt și descriptiv (maximum 50 caractere) pentru o conversație bazat pe următorul mesaj al utilizatorului.

Mesaj utilizator: {user_message}

Cerințe STRICTE:
- Titlul trebuie să fie scurt, concis și descriptiv (max 50 caractere)
- Trebuie să reflecte ESENȚA întrebării sau subiectului, NU să fie o copie a mesajului
- Transformă mesajul într-un titlu clar și relevant (ex: "am facut accident cu masina" → "Accident rutier" sau "Accident de mașină")
- Folosește limba română
- Nu include ghilimele, puncte finale sau caractere speciale
- NU copia mesajul exact - creează un titlu nou care să rezume subiectul
- Dacă mesajul este despre un subiect specific, extrage subiectul (ex: "pensie", "accident", "ajutor social")
- Titlul trebuie să fie util pentru a identifica conversația în listă

Exemple:
- "am facut accident cu masina" → "Accident rutier"
- "ce drepturi am ca pensionar" → "Drepturi pensionari"
- "unde trebuie sa ma duc sa depun cererea" → "Depunere cerere"
- "sunt o persoana in varsta cu pensie de 2000 de lei" → "Pensie persoane în vârstă"

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

