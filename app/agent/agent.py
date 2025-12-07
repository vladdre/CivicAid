"""
Agent cognitiv funcțional folosind OpenAI Functions Agent.

Obiectiv: Asamblarea componentelor într-un sistem cognitiv funcțional.

Logica de Execuție:
1. Input: User Message
2. LLM Processing: GPT-4o analizează input-ul și prompt-ul de sistem
3. Router (Decizie):
   - Are nevoie de lege? -> Cheamă consult_legislation
   - Are nevoie de adresă? -> Cheamă SQL Tool
   - Este doar conversație ("Salut")? -> Răspunde direct
4. Action: Execută tool-ul selectat
5. Observation: Primește rezultatul (text din lege sau rânduri din SQL)
6. Final Response: Sintetizează observația într-un răspuns natural pentru utilizator
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI

from app.agent.tools import TOOLS_DEFINITIONS, TOOLS_MAP

load_dotenv()


class Agent:
    """
    Agent cognitiv funcțional care folosește OpenAI Functions pentru a decide
    ce tool-uri să folosească și să răspundă utilizatorului.
    """
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.3):
        """
        Inițializează agentul.
        
        Args:
            model: Modelul OpenAI de folosit (default: gpt-4o)
            temperature: Temperatura pentru generare (default: 0.3)
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY nu este setată în .env")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.conversation_history: List[Dict[str, str]] = []
        
        # System prompt
        self.system_prompt = """Ești CivicAID, un asistent juridic inteligent care ajută cetățenii români să înțeleagă drepturile și obligațiile lor legale.

Rolul tău:
1. Analizează întrebările utilizatorilor și determină ce informații sunt necesare
2. Folosește tool-urile disponibile pentru a găsi informații relevante:
   - consult_legislation: pentru întrebări despre legi, drepturi legale, proceduri juridice
   - get_institution_address: pentru întrebări despre unde să meargă, adrese de instituții, program de lucru
3. Sintetizează răspunsurile într-un mod clar, concis și util pentru utilizator

Reguli:
- Dacă utilizatorul salută sau face o întrebare generală de conversație, răspunde direct fără tool-uri
- Dacă utilizatorul întreabă despre legi sau drepturi, folosește consult_legislation
- Dacă utilizatorul întreabă despre adrese, instituții sau unde să meargă, folosește get_institution_address
- Răspunsurile trebuie să fie clare, concise și utile
- Nu adăuga informații care nu sunt în rezultatele tool-urilor
- Folosește limba română"""
    
    def add_to_history(self, role: str, content: str):
        """
        Adaugă un mesaj în istoricul conversației.
        
        Args:
            role: 'user' sau 'assistant'
            content: Conținutul mesajului
        """
        self.conversation_history.append({"role": role, "content": content})
    
    def clear_history(self):
        """Șterge istoricul conversației."""
        self.conversation_history = []
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execută un tool specificat.
        
        Args:
            tool_name: Numele tool-ului
            arguments: Argumentele pentru tool
            
        Returns:
            Rezultatul execuției tool-ului
        """
        if tool_name not in TOOLS_MAP:
            return f"❌ Tool '{tool_name}' nu este disponibil."
        
        try:
            tool_func = TOOLS_MAP[tool_name]
            # Extrage user_message din arguments
            user_message = arguments.get("user_message", "")
            
            # Pasează istoricul conversației (fără ultimul mesaj care este cel curent)
            conversation_history = self.conversation_history[:-1] if len(self.conversation_history) > 1 else None
            
            result = tool_func(user_message, conversation_history)
            return result
        except Exception as e:
            return f"❌ Eroare la executarea tool-ului '{tool_name}': {str(e)}"
    
    def process(self, user_message: str, max_iterations: int = 5) -> str:
        """
        Procesează un mesaj de la utilizator folosind arhitectura OpenAI Functions Agent.
        
        Args:
            user_message: Mesajul utilizatorului
            max_iterations: Numărul maxim de iterații (pentru multi-turn tool calling)
            
        Returns:
            Răspunsul final al agentului
        """
        # Adaugă mesajul utilizatorului în istoric
        self.add_to_history("user", user_message)
        
        # Construiește mesajele pentru API
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history
        
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Apel API cu tool-uri
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS_DEFINITIONS,
                tool_choice="auto",  # Lăsăm modelul să decidă
                temperature=self.temperature
            )
            
            message = response.choices[0].message
            
            # Adaugă răspunsul în messages pentru context
            messages.append(message)
            
            # Verifică dacă modelul vrea să folosească un tool
            if message.tool_calls:
                # Execută toate tool-urile cerute
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    import json
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    # Execută tool-ul
                    tool_result = self._execute_tool(tool_name, tool_args)
                    
                    # Adaugă rezultatul în messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # Continuă loop-ul pentru a permite modelului să sintetizeze răspunsul
                continue
            else:
                # Modelul a dat un răspuns final
                final_response = message.content
                
                # Adaugă răspunsul în istoric
                self.add_to_history("assistant", final_response)
                
                return final_response
        
        # Dacă am ajuns aici, am depășit numărul maxim de iterații
        return "❌ Am depășit numărul maxim de iterații. Te rog reîncearcă cu o întrebare mai simplă."
    
    def chat(self, user_message: str) -> str:
        """
        Metodă simplificată pentru chat - alias pentru process.
        
        Args:
            user_message: Mesajul utilizatorului
            
        Returns:
            Răspunsul agentului
        """
        return self.process(user_message)


def main():
    """
    Funcție de test pentru agent.
    """
    print("=" * 70)
    print("🤖 CivicAID Agent - Test")
    print("=" * 70)
    print()
    
    agent = Agent()
    
    # Exemple de test
    test_messages = [
        "Salut!",
        "Ce drepturi am ca pensionar cu pensie de 2000 de lei?",
        "Unde trebuie să mă duc să depun cererea de pensie?",
    ]
    
    for msg in test_messages:
        print(f"\n👤 Utilizator: {msg}")
        print("-" * 70)
        response = agent.chat(msg)
        print(f"🤖 Agent: {response}")
        print("=" * 70)


if __name__ == "__main__":
    main()

