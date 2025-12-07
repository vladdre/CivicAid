"""
Script pentru găsirea articolelor de lege relevante pe baza unui mesaj simplu/informal.

Acest script permite utilizatorului să introducă un mesaj simplu (ex: "Am avut un accident de mașină")
și primește înapoi articolele de lege relevante din vector store.

Usage:
    # Mod interactiv (întreabă utilizatorul)
    python scripts/find_law.py
    
    # Mod CLI (mesajul ca argument)
    python scripts/find_law.py "Am avut un accident de mașină"
"""

import os
import sys
from pathlib import Path
from typing import Tuple
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

# Configuration
VECTOR_STORE_DIR = Path(__file__).parent.parent / "data" / "vector_store"
COLLECTION_NAME = "civicaid_laws"

# Cache pentru vector store instance (lazy loading - optimizare)
_vector_store_instance = None
_vector_store_embeddings = None


def extract_keywords_and_query(user_message: str, api_key: str, conversation_history: list = None, verbose: bool = False) -> Tuple[str, bool]:
    """
    Încearcă să transforme un mesaj informal într-un query mai bun pentru căutare semantică.
    
    Folosește OpenAI pentru a extrage cuvinte cheie și a reformula mesajul
    într-un format mai potrivit pentru căutare în documente legale.
    
    Args:
        user_message: Mesajul informal al utilizatorului
        api_key: OpenAI API key
        conversation_history: Listă de mesaje anterioare din conversație (opțional)
                           Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        
    Returns:
        Tuple (query, was_improved):
        - query: Query-ul optimizat sau original
        - was_improved: True dacă query-ul a fost îmbunătățit, False dacă nu s-a putut îmbunătăți
    """
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",  # Model rapid și ieftin
            temperature=0.3,
            openai_api_key=api_key
        )
        
        # Construiește contextul conversației dacă există
        context_section = ""
        if conversation_history and len(conversation_history) > 0:
            # Include ultimele 3-4 mesaje pentru context (evită prompt-uri prea lungi)
            recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            context_lines = []
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    context_lines.append(f"Utilizator: {content}")
                elif role == "assistant":
                    # Trunchiază răspunsurile lungi pentru a nu depăși limitele
                    content_preview = content[:200] + "..." if len(content) > 200 else content
                    context_lines.append(f"Asistent: {content_preview}")
            
            if context_lines:
                context_section = f"""

Context conversație anterioară:
{chr(10).join(context_lines)}

IMPORTANT: Dacă mesajul curent este o întrebare de follow-up (ex: "Ce înseamnă asta?", "Mai multe detalii", "Unde găsesc asta?"), 
folosește contextul pentru a înțelege la ce se referă utilizatorul și transformă întrebarea într-un query complet și clar.
"""
        
        # Creăm prompt-ul combinat ca string
        full_prompt = f"""Ești un asistent care transformă mesaje informale în query-uri optimizate 
pentru căutare în documente legale românești.

Task: Analizează mesajul utilizatorului și transformă-l într-un query optimizat pentru căutare semantică 
în legi, articole și documente juridice românești.{context_section}

Reguli STRICTE:
1. Dacă mesajul este DEJA clar, specific și conține termeni juridici relevanți, răspunde cu "NU_POATE_FI_IMBUNATATIT"
2. Dacă mesajul este informal, vag sau lipsesc termeni juridici, transformă-l într-un query optimizat
3. Dacă mesajul este o întrebare de follow-up, folosește contextul pentru a construi un query complet
4. Păstrează sensul original
5. Adaugă termeni juridici relevanți DOAR dacă îmbunătățesc căutarea
6. Fă query-ul clar și specific pentru documente legale românești
7. Răspunde DOAR cu query-ul optimizat SAU cu "NU_POATE_FI_IMBUNATIT", fără explicații

Exemple:
- "accident de mașină" → "accident rutier, răspundere civilă, daune materiale"
- "bani ajutor" → "ajutor social, venit minim garantat, asistență socială"
- "ARTICOLUL 1 din Constituție" → NU_POATE_FI_IMBUNATIT
- "răspundere civilă pentru daune" → NU_POATE_FI_IMBUNATIT
- Follow-up: "Unde găsesc asta?" (după răspuns despre pensie) → "instituții pensie, unde depun cererea pensie, adrese pensie"

Mesaj utilizator: {user_message}

Răspuns:"""
        
        # Folosim invoke direct cu string
        response = llm.invoke(full_prompt)
        
        # Extrage doar textul răspunsului
        optimized_query = response.content.strip()
        
        # Verifică dacă LLM-ul a decis că nu poate fi îmbunătățit
        if "NU_POATE_FI_IMBUNATIT" in optimized_query.upper() or optimized_query.upper().startswith("NU"):
            if verbose:
                print(f"ℹ️  Query-ul nu poate fi îmbunătățit cu informații utile.")
                print(f"   Folosesc mesajul original: \"{user_message}\"")
            return user_message, False
        
        # Verifică dacă query-ul optimizat este prea similar cu originalul
        # (dacă diferența este minimă, nu are sens să folosim versiunea optimizată)
        original_lower = user_message.lower().strip()
        optimized_lower = optimized_query.lower().strip()
        
        # Dacă sunt identice sau foarte similare, nu a fost îmbunătățit
        if original_lower == optimized_lower or len(set(original_lower.split()) & set(optimized_lower.split())) / max(len(original_lower.split()), 1) > 0.9:
            if verbose:
                print(f"ℹ️  Query-ul optimizat este prea similar cu originalul.")
                print(f"   Folosesc mesajul original: \"{user_message}\"")
            return user_message, False
        
        # Query-ul a fost îmbunătățit
        if verbose:
            print(f"✅ Query îmbunătățit: \"{user_message}\" → \"{optimized_query}\"")
        return optimized_query, True
        
    except Exception as e:
        if verbose:
            print(f"⚠️  Eroare la optimizarea query-ului: {e}")
            print(f"   Folosesc mesajul original: \"{user_message}\"")
        return user_message, False


def find_relevant_laws(user_message: str, k: int = 5, use_optimization: bool = True, conversation_history: list = None, verbose: bool = False) -> list:
    """
    Găsește articole de lege relevante pentru un mesaj dat.
    
    Args:
        user_message: Mesajul utilizatorului (poate fi informal)
        k: Numărul de rezultate de returnat (default: 5)
        use_optimization: Dacă să optimizeze query-ul folosind LLM (default: True)
        conversation_history: Istoricul conversației (opțional)
        verbose: Dacă True, afișează print-uri (default: False pentru API calls)
        
    Returns:
        Listă de documente relevante
    """
    if verbose:
        print("=" * 70)
        print("🔎 Căutare Articole de Lege Relevante")
        print("=" * 70)
        print(f"\n📝 Mesaj primit: \"{user_message}\"\n")
    
    # Verifică dacă vector store-ul există
    if not VECTOR_STORE_DIR.exists():
        if verbose:
            print(f"❌ Vector store nu există la: {VECTOR_STORE_DIR}")
            print("   Rulează mai întâi: python scripts/ingest_laws.py")
        return []
    
    # Verifică API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        if verbose:
            print("❌ OPENAI_API_KEY nu este setată în .env")
        return []
    
    # Încarcă vector store-ul (lazy loading - reutilizează instanța dacă există)
    global _vector_store_instance, _vector_store_embeddings
    
    try:
        if _vector_store_instance is None:
            # Creează embeddings și vector store doar prima dată
            _vector_store_embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key
            )
            _vector_store_instance = Chroma(
                persist_directory=str(VECTOR_STORE_DIR),
                embedding_function=_vector_store_embeddings,
                collection_name=COLLECTION_NAME
            )
        
        vector_store = _vector_store_instance
    except Exception as e:
        if verbose:
            print(f"❌ Eroare la încărcarea vector store-ului: {e}")
        return []
    
    # Încearcă să optimizeze query-ul dacă e necesar (cu context din conversație)
    search_query = user_message
    was_improved = False
    if use_optimization:
        search_query, was_improved = extract_keywords_and_query(user_message, api_key, conversation_history, verbose=verbose)
        if verbose and not was_improved:
            print()  # Linie goală pentru claritate
    
    # Caută în vector store cu scoruri
    if verbose:
        print(f"\n🔍 Căutare în vector store cu query: \"{search_query}\"...\n")
    
    try:
        # Folosim similarity_search_with_score pentru a vedea relevanța
        results_with_scores = vector_store.similarity_search_with_score(search_query, k=k)
        
        if not results_with_scores:
            if verbose:
                print("⚠️  Nu s-au găsit rezultate relevante.")
            return []
        
        # Afișează scorurile pentru debugging (doar dacă verbose)
        if verbose:
            print("📊 Scoruri de similaritate (mai mic = mai relevant):")
            for i, (doc, score) in enumerate(results_with_scores, 1):
                source = doc.metadata.get("source", "Necunoscut")
                print(f"   {i}. [{source}] Score: {score:.4f}")
            print()
        
        # Extrage doar documentele (fără scoruri) pentru return
        results = [doc for doc, score in results_with_scores]
        
        return results
        
    except Exception as e:
        print(f"❌ Eroare la căutare: {e}")
        return []


def format_results(results: list) -> str:
    """
    Formatează rezultatele într-un format citibil.
    
    Args:
        results: Listă de documente
        
    Returns:
        Text formatat
    """
    if not results:
        return "Nu s-au găsit rezultate."
    
    output = []
    output.append(f"\n{'='*70}")
    output.append(f"📚 Articole de Lege Relevante ({len(results)} rezultate)")
    output.append(f"{'='*70}\n")
    
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("source", "Necunoscut")
        file_path = doc.metadata.get("file_path", "")
        
        # Extrage numărul articolului dacă există
        content = doc.page_content
        article_match = None
        if "ARTICOLUL" in content or "Articolul" in content:
            # Încearcă să găsească "ARTICOLUL X" sau "Articolul X"
            import re
            article_pattern = r'(?:ARTICOLUL|Articolul)\s+(\d+[a-z]?)'
            match = re.search(article_pattern, content[:200])
            if match:
                article_match = match.group(0)
        
        output.append(f"{'─'*70}")
        output.append(f"📄 Rezultat {i}/{len(results)}")
        output.append(f"{'─'*70}")
        output.append(f"📁 Sursă: {source}")
        if article_match:
            output.append(f"📑 {article_match}")
        if file_path:
            output.append(f"📂 Cale: {file_path}")
        output.append(f"\n📝 Conținut:")
        output.append(f"{content}")
        output.append("")
    
    output.append(f"{'='*70}")
    output.append("✅ Căutare completă!")
    output.append(f"{'='*70}\n")
    
    return "\n".join(output)


def main():
    """Funcția principală."""
    
    # Determină modul de rulare
    if len(sys.argv) > 1:
        # Mod CLI: mesajul este primul argument
        user_message = " ".join(sys.argv[1:])
    else:
        # Mod interactiv: întreabă utilizatorul
        print("=" * 70)
        print("🔎 Găsire Articole de Lege Relevante")
        print("=" * 70)
        print("\nIntrodu mesajul tău (ex: 'Am avut un accident de mașină'):")
        print("(Apasă Enter după ce ai terminat, sau Ctrl+D pentru a ieși)\n")
        
        try:
            user_message = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 La revedere!")
            return
        
        if not user_message:
            print("❌ Mesajul nu poate fi gol.")
            return
    
    # Găsește articolele relevante
    # use_optimization=True: încearcă să îmbunătățească query-ul, dar folosește originalul dacă nu se poate
    results = find_relevant_laws(user_message, k=5, use_optimization=True)
    
    # Afișează rezultatele
    if results:
        formatted_output = format_results(results)
        print(formatted_output)
        
        # Opțional: salvează rezultatele într-un fișier
        output_file = Path(__file__).parent.parent / "data" / "search_results.txt"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_output)
            print(f"💾 Rezultatele au fost salvate în: {output_file}")
        except Exception as e:
            print(f"⚠️  Nu s-au putut salva rezultatele: {e}")
    else:
        print("\n❌ Nu s-au găsit articole de lege relevante.")
        print("   Verifică că:")
        print("   1. Ai rulat 'python scripts/ingest_laws.py' pentru a crea vector store-ul")
        print("   2. Ai adăugat PDF-uri cu legi în 'data/raw_laws/'")
        print("   3. Mesajul tău este relevant pentru conținutul legilor indexate")


if __name__ == "__main__":
    main()

