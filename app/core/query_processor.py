"""
Script principal pentru CivicAid - Orchestrează crearea vectorilor și căutarea legilor.

Usage:
    python main.py "Am avut un accident de mașină"
    
Funcționalitate:
1. Verifică dacă există vector store
2. Dacă nu există, creează vectorii rulând ingest_laws.py
3. Rulează find_law.py cu mesajul dat
4. Scrie outputul în output.txt
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Add app directory to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "app"))

# Load environment variables
load_dotenv()

# Configuration
VECTOR_STORE_DIR = PROJECT_ROOT / "data" / "vector_store"
OUTPUT_FILE = PROJECT_ROOT / "data" / "output.txt"

# Cache pentru verificarea vector store-ului (optimizare)
_vector_store_cache = {"exists": None, "checked": False}


def check_vector_store_exists() -> bool:
    """
    Verifică dacă vector store-ul există și conține date.
    
    Folosește cache pentru a evita verificări redundante (optimizare).
    
    Returns:
        True dacă vector store-ul există și are conținut, False altfel
    """
    global _vector_store_cache
    
    # Returnează din cache dacă a fost deja verificat
    if _vector_store_cache["checked"]:
        return _vector_store_cache["exists"]
    
    # Verificare efectivă
    if not VECTOR_STORE_DIR.exists():
        _vector_store_cache["exists"] = False
        _vector_store_cache["checked"] = True
        return False
    
    # Verifică dacă directorul nu este gol
    # ChromaDB creează mai multe fișiere, deci verificăm dacă există cel puțin unul
    try:
        files = list(VECTOR_STORE_DIR.iterdir())
        if len(files) == 0:
            _vector_store_cache["exists"] = False
            _vector_store_cache["checked"] = True
            return False
        
        # Verifică dacă există fișiere relevante ChromaDB
        # ChromaDB creează de obicei fișiere .sqlite sau directoare
        has_content = any(
            f.is_file() and (f.suffix in ['.sqlite', '.db'] or f.name.startswith('chroma'))
            or f.is_dir()
            for f in files
        )
        _vector_store_cache["exists"] = has_content
        _vector_store_cache["checked"] = True
        return has_content
    except Exception:
        _vector_store_cache["exists"] = False
        _vector_store_cache["checked"] = True
        return False


def reset_vector_store_cache():
    """
    Resetează cache-ul pentru vector store (util când se creează un vector store nou).
    """
    global _vector_store_cache
    _vector_store_cache = {"exists": None, "checked": False}


def create_vector_store():
    """
    Creează vector store-ul rulând scriptul ingest_laws.py.
    """
    print("=" * 70)
    print("📚 Creare Vector Store")
    print("=" * 70)
    print("\n⚠️  Vector store-ul nu există sau este gol.")
    print("🚀 Pornesc crearea vectorilor din PDF-uri...\n")
    
    # Import funcțiile din ingest_laws.py
    try:
        from app.scripts.ingest_laws import (
            load_pdfs,
            split_documents,
            create_vector_store as create_vs,
            RAW_LAWS_DIR,
            VECTOR_STORE_DIR as VS_DIR
        )
        
        # Step 1: Load PDFs
        documents = load_pdfs(RAW_LAWS_DIR)
        
        if not documents:
            print("\n❌ Nu există PDF-uri în data/raw_laws/")
            print("   Adaugă PDF-uri cu legi în data/raw_laws/ și rulează din nou.")
            sys.exit(1)
        
        # Step 2: Split into chunks
        chunks = split_documents(documents)
        
        if not chunks:
            print("\n❌ Nu s-au creat chunks. Ieșire.")
            sys.exit(1)
        
        # Step 3: Create embeddings and store in ChromaDB
        vector_store = create_vs(chunks, VS_DIR)
        
        if vector_store:
            print("\n✅ Vector store creat cu succes!\n")
            # Resetează cache-ul pentru că am creat un vector store nou
            reset_vector_store_cache()
        else:
            print("\n❌ Eroare la crearea vector store-ului.")
            sys.exit(1)
            
    except ImportError as e:
        print(f"❌ Eroare la importul funcțiilor: {e}")
        print("   Verifică că scripts/ingest_laws.py există și este corect.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Eroare la crearea vector store-ului: {e}")
        sys.exit(1)


def run_find_law(user_message: str, conversation_history: list = None, verbose: bool = False) -> tuple[str, Optional[list]]:
    """
    Rulează find_law.py cu mesajul dat și returnează outputul și rezultatele.
    
    Args:
        user_message: Mesajul pentru căutare
        conversation_history: Istoricul conversației (opțional)
        verbose: Dacă True, afișează print-uri (default: False pentru API calls)
        
    Returns:
        Tuple (output_formatat, lista_rezultate):
        - output_formatat: Output-ul formatat ca string
        - lista_rezultate: Lista de documente sau None dacă nu există
    """
    if verbose:
        print("=" * 70)
        print("🔎 Căutare Articole de Lege")
        print("=" * 70)
        print()
    
    # Import funcțiile din find_law.py
    try:
        from app.scripts.find_law import find_relevant_laws, format_results
        
        # Găsește articolele relevante (cu context din conversație)
        results = find_relevant_laws(user_message, k=5, use_optimization=True, conversation_history=conversation_history, verbose=verbose)
        
        # Formatează rezultatele
        if results:
            output = format_results(results)
            return output, results
        else:
            return "❌ Nu s-au găsit articole de lege relevante.", None
            
    except ImportError as e:
        error_msg = f"❌ Eroare la importul funcțiilor: {e}\n   Verifică că scripts/find_law.py există și este corect."
        if verbose:
            print(error_msg)
        return error_msg, None
    except Exception as e:
        error_msg = f"❌ Eroare la căutare: {e}"
        if verbose:
            print(error_msg)
        return error_msg, None


def summarize_results(results: list, user_query: str, verbose: bool = False) -> str:
    """
    Sintetizează rezultatele din cele 5 chunks într-un rezumat concis.
    
    Args:
        results: Lista de documente (chunks) relevante
        user_query: Query-ul original al utilizatorului
        
    Returns:
        Rezumat sintetizat ca string
    """
    if not results:
        return "Nu s-au găsit rezultate de rezumat."
    
    # Extrage conținutul din toate chunks-urile
    all_content = []
    sources = []
    
    for doc in results:
        content = doc.page_content.strip()
        source = doc.metadata.get("source", "Necunoscut")
        all_content.append(content)
        sources.append(source)
    
    # Combină conținutul pentru a-l trimite la LLM
    combined_content = "\n\n---\n\n".join([
        f"[Sursă: {source}]\n{content}" 
        for source, content in zip(sources, all_content)
    ])
    
    # Verifică API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "⚠️  OPENAI_API_KEY nu este setată. Nu pot genera rezumat."
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",  # Model rapid și eficient
            temperature=0.3,  # Temperatură scăzută pentru consistență
            openai_api_key=api_key
        )
        
        # Prompt pentru rezumat
        prompt = f"""Ești un asistent juridic care sintetizează informații din documente legale românești.

Task: Creează un rezumat concis și precis al informațiilor relevante pentru întrebarea utilizatorului.

Întrebare utilizator: {user_query}

Informații găsite în documente:
{combined_content}

Reguli STRICTE pentru rezumat:
1. Păstrează DOAR informațiile care sunt EXACT în documentele furnizate
2. NU adăuga informații care nu sunt în documentele furnizate
3. NU adăuga concluzii, recomandări sau sugestii care nu sunt în documente
4. NU adăuga fraze precum "Este important de menționat", "Este recomandat", "Pentru detalii specifice consultați" sau similare
5. NU adăuga informații generale sau cunoștințe generale despre subiect
6. Folosește formulare concisă și clară
7. Păstrează termenii juridici importanți (ex: "ARTICOLUL X", "răspundere civilă")
8. Dacă există articole de lege, menționează-le direct (ex: "ARTICOLUL 1356 prevede...")
9. NU folosi cuvântul "Conform" sau "conform" în rezumat
10. NU menționa sursele sau numele documentelor la final (ex: "Conform [nume document]")
11. NU adăuga referințe la documente în formatul "Conform [nume document]" sau similar
12. Dacă informațiile sunt incomplete în documente, NU adăuga sugestii sau recomandări

Format rezumat:
- Începe direct cu informațiile relevante din documente
- Folosește bullet points pentru claritate
- Menționează articolele de lege direct, fără "Conform" (ex: "ARTICOLUL 1356 prevede..." sau "Codul fiscal, ARTICOLUL 154...")
- NU adăuga referințe la documente la final
- NU adăuga concluzii sau recomandări care nu sunt în documente

IMPORTANT: 
- Rezumatul trebuie să conțină DOAR informațiile care sunt în documentele furnizate
- NU adăuga niciodată concluzii, recomandări, sugestii sau informații generale
- NU adăuga linii precum "Conform [nume document]" sau "Este recomandat să consultați"
- Dacă documentele nu conțin informații complete, spune doar ce este în documente, fără să sugerezi să se consulte altundeva

Rezumat:"""
        
        if verbose:
            print("\n📝 Generare rezumat sintetizat...")
        response = llm.invoke(prompt)
        summary = response.content.strip()
        
        return summary
        
    except Exception as e:
        return f"⚠️  Eroare la generarea rezumatului: {e}"


def write_output_to_file(output: str, output_file: Path):
    """
    Scrie outputul în fișier, suprascriind orice conținut existent.
    
    Args:
        output: Textul de scris
        output_file: Calea către fișierul de output
    """
    try:
        # Șterge fișierul dacă există pentru a asigura suprascrierea completă
        if output_file.exists():
            output_file.unlink()
        
        # Scrie noul conținut (modul "w" creează sau suprascrie fișierul)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        
        # Verifică că fișierul a fost scris corect
        if output_file.exists() and output_file.stat().st_size > 0:
            print(f"💾 Output salvat în: {output_file} ({output_file.stat().st_size} bytes)")
        else:
            print(f"⚠️  Avertisment: Fișierul nu pare să fie scris corect")
            
    except Exception as e:
        print(f"❌ Eroare la scrierea în fișier: {e}")
        import traceback
        traceback.print_exc()


def process_query(user_message: str, conversation_history: list = None, verbose: bool = False) -> str:
    """
    Procesează un query și returnează rezultatul formatat.
    
    Această funcție poate fi apelată programatic (ex: din frontend).
    
    Args:
        user_message: Mesajul pentru căutare
        conversation_history: Listă de mesaje anterioare din conversație (opțional)
                           Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        verbose: Dacă True, afișează print-uri (default: False pentru API calls)
        
    Returns:
        Output-ul formatat ca string
    """
    if verbose:
        print("=" * 70)
        print("🚀 CivicAid - Main Script")
        print("=" * 70)
        print(f"\n📝 Mesaj primit: \"{user_message}\"\n")
    
    # Step 1: Verifică dacă vector store-ul există (cache-ul face asta rapid)
    if verbose:
        print("🔍 Verificare vector store...")
    if not check_vector_store_exists():
        if verbose:
            print("   ⚠️  Vector store-ul nu există sau este gol.")
        create_vector_store()
    elif verbose:
        print("   ✅ Vector store-ul există și are conținut.\n")
    
    # Step 2: Rulează find_law
    output, results = run_find_law(user_message, verbose=verbose)
    
    # Step 3: Generează rezumat sintetizat
    summary = ""
    if results:
        if verbose:
            print("\n" + "=" * 70)
            print("📝 Sintetizare Rezultate")
            print("=" * 70)
        summary = summarize_results(results, user_message, verbose=verbose)
        if verbose:
            print("✅ Rezumat generat!\n")
    
    # Step 4: Combină output-ul detaliat cu rezumatul
    final_output = ""
    if summary:
        final_output = f"""
{'='*70}
📋 REZUMAT SINTETIZAT
{'='*70}

{summary}
"""
    else:
        final_output = output
    
    # Step 5: Scrie outputul în fișier (doar pentru CLI, nu pentru API)
    # Comentat pentru optimizare - nu este necesar pentru API calls
    # write_output_to_file(final_output, OUTPUT_FILE)
    
    return final_output


# Note: main() function moved to root main.py for CLI entry point


