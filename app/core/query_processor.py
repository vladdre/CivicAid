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
import json
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
VECTOR_STORE_JSON_DIR = PROJECT_ROOT / "data" / "vector_store_json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "output.txt"
LEGI_JSON = PROJECT_ROOT / "legi.json"
CHECKPOINT_JSON = PROJECT_ROOT / "checkpoint.json"

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


def summarize_results(results: list, user_query: str, conversation_history: list = None, verbose: bool = False) -> str:
    """
    Sintetizează rezultatele din cele 5 chunks într-un rezumat concis.
    
    Args:
        results: Lista de documente (chunks) relevante
        user_query: Query-ul original al utilizatorului
        conversation_history: Istoricul conversației (opțional) pentru context
        verbose: Dacă True, afișează print-uri
        
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
        
        # Construiește contextul conversației dacă există
        context_section = ""
        if conversation_history and len(conversation_history) > 0:
            # Include ultimele 3-4 mesaje pentru context
            recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            context_lines = []
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    context_lines.append(f"Utilizator: {content}")
                elif role == "assistant":
                    # Trunchiază răspunsurile lungi
                    content_preview = content[:200] + "..." if len(content) > 200 else content
                    context_lines.append(f"Asistent: {content_preview}")
            
            if context_lines:
                context_section = f"""

Context conversație anterioară:
{chr(10).join(context_lines)}

IMPORTANT: Dacă întrebarea este o întrebare de follow-up, folosește contextul pentru a înțelege la ce se referă utilizatorul.
"""
        
        # Prompt pentru rezumat
        prompt = f"""Ești un asistent juridic care sintetizează informații din documente legale românești.

Task: Creează un rezumat concis și precis al informațiilor relevante pentru întrebarea utilizatorului.{context_section}

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


def is_summary_relevant(summary: str, user_query: str, api_key: str) -> bool:
    """
    Verifică dacă rezumatul generat este relevant pentru întrebarea utilizatorului.
    
    Args:
        summary: Rezumatul generat
        user_query: Întrebarea utilizatorului
        api_key: OpenAI API key
        
    Returns:
        True dacă rezumatul este relevant, False altfel
    """
    if not summary or len(summary.strip()) < 50:
        return False
    
    # Mesaje care indică că rezumatul nu este relevant
    irrelevant_indicators = [
        "nu s-au găsit",
        "nu am găsit",
        "nu există",
        "nu s-au găsit rezultate",
        "nu s-au găsit articole",
        "nu s-au găsit informații",
        "nu am informații",
        "nu pot",
        "nu pot genera",
        "nu pot găsi",
    ]
    
    summary_lower = summary.lower()
    for indicator in irrelevant_indicators:
        if indicator in summary_lower:
            return False
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=api_key
        )
        
        prompt = f"""Evaluează dacă următorul rezumat este relevant pentru întrebarea utilizatorului.

Întrebare utilizator: {user_query}

Rezumat generat:
{summary}

Răspunde DOAR cu "DA" dacă rezumatul conține informații relevante și utile pentru întrebare, sau "NU" dacă rezumatul nu este relevant, este prea general, sau nu răspunde la întrebare.

Răspuns (DA/NU):"""
        
        response = llm.invoke(prompt)
        answer = response.content.strip().upper()
        
        return answer.startswith("DA")
        
    except Exception as e:
        # În caz de eroare, consideră că rezumatul este relevant pentru a nu bloca procesarea
        return True


def search_in_json_files(user_query: str, api_key: str, verbose: bool = False) -> Optional[str]:
    """
    Caută informații relevante în vector store-ul JSON (din legi.json).
    Folosește vector store-ul JSON dacă există, altfel caută direct în JSON.
    
    Args:
        user_query: Întrebarea utilizatorului
        api_key: OpenAI API key
        verbose: Dacă True, afișează print-uri
        
    Returns:
        Text relevant găsit sau None dacă nu s-a găsit nimic relevant
    """
    # Încearcă să folosească vector store-ul JSON (prioritate)
    if VECTOR_STORE_JSON_DIR.exists():
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_community.vectorstores import Chroma
            
            if verbose:
                print("   🔍 Căutare în vector store JSON...")
            
            # Încarcă vector store-ul JSON
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key
            )
            
            vector_store = Chroma(
                persist_directory=str(VECTOR_STORE_JSON_DIR),
                embedding_function=embeddings,
                collection_name="civicaid_json_laws"
            )
            
            # Caută în vector store
            results = vector_store.similarity_search_with_score(user_query, k=3)
            
            if not results or len(results) == 0:
                if verbose:
                    print("   ⚠️  Nu s-au găsit rezultate în vector store JSON")
                return None
            
            # Extrage conținutul și metadata
            relevant_texts = []
            for doc, score in results:
                # Filtrează rezultatele cu scor prea mic (relevanță scăzută)
                if score > 1.5:  # Threshold pentru relevanță
                    continue
                
                law_id = doc.metadata.get('law_id', 'Necunoscut')
                content = doc.page_content
                relevant_texts.append(f"[{law_id}]\n{content}")
            
            if not relevant_texts:
                if verbose:
                    print("   ⚠️  Nu s-au găsit rezultate relevante în vector store JSON")
                return None
            
            # Sintetizează rezultatele
            combined_text = "\n\n---\n\n".join(relevant_texts)
            
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                openai_api_key=api_key
            )
            
            synthesis_prompt = f"""Ești un asistent juridic. Sintetizează informațiile relevante găsite în documente pentru întrebarea utilizatorului.

Întrebare utilizator: {user_query}

Informații găsite în documente:
{combined_text}

Task: Creează un rezumat concis și precis al informațiilor relevante pentru întrebare. Dacă informațiile nu sunt relevante sau nu răspund la întrebare, returnează DOAR "NU_SUNT_RELEVANTE".

Rezumat:"""
            
            response = llm.invoke(synthesis_prompt)
            result = response.content.strip()
            
            if result.upper() == "NU_SUNT_RELEVANTE" or len(result) < 50:
                if verbose:
                    print("   ⚠️  Rezultatele nu sunt relevante")
                return None
            
            if verbose:
                print("   ✅ Informații relevante găsite în vector store JSON")
            
            return result
            
        except Exception as e:
            if verbose:
                print(f"   ⚠️  Eroare la căutarea în vector store JSON: {e}")
                print("   🔄 Revenire la căutare directă în JSON...")
            # Continuă cu căutarea directă în JSON dacă vector store-ul nu funcționează
    
    # Fallback: căutare directă în JSON (doar legi.json, checkpoint.json este doar pentru rezervă)
    if not LEGI_JSON.exists():
        return None
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=api_key
        )
        
        if verbose:
            print("   🔍 Căutare directă în legi.json...")
        
        # Extrage cuvinte cheie din query pentru căutare
        keywords_prompt = f"""Extrage cuvintele cheie principale din următoarea întrebare pentru căutare în documente legale.

Întrebare: {user_query}

Returnează DOAR 3-5 cuvinte cheie separate prin virgulă, fără explicații.
Cuvinte cheie:"""
        
        keywords_response = llm.invoke(keywords_prompt)
        keywords = keywords_response.content.strip().lower()
        keyword_list = [k.strip() for k in keywords.split(",")][:5]
        
        # Caută în legi.json
        relevant_texts = []
        
        try:
            with open(LEGI_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Caută în structura JSON
            def search_recursive(obj, path="", depth=0):
                """Caută recursiv în structura JSON"""
                if depth > 5:  # Limitează adâncimea pentru performanță
                    return []
                
                found = []
                
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        
                        # Verifică cheia
                        key_lower = str(key).lower()
                        if any(kw in key_lower for kw in keyword_list):
                            if isinstance(value, str) and len(value) > 100:
                                found.append((current_path, value[:2000]))  # Limitează lungimea
                        
                        # Verifică valoarea
                        if isinstance(value, str):
                            value_lower = value.lower()
                            if any(kw in value_lower for kw in keyword_list):
                                if len(value) > 100:
                                    found.append((current_path, value[:2000]))
                        elif isinstance(value, (dict, list)):
                            found.extend(search_recursive(value, current_path, depth + 1))
                
                elif isinstance(obj, list):
                    for i, item in enumerate(obj[:10]):  # Limitează numărul de elemente
                        found.extend(search_recursive(item, f"{path}[{i}]", depth + 1))
                
                return found
            
            found_texts = search_recursive(data)
            
            if found_texts:
                # Selectează cele mai relevante (primele 3)
                for path, text in found_texts[:3]:
                    relevant_texts.append(f"[legi.json:{path}]\n{text}")
            
        except Exception as e:
            if verbose:
                print(f"   ⚠️  Eroare la citirea legi.json: {e}")
            return None
        
        if not relevant_texts:
            return None
        
        # Sintetizează rezultatele găsite
        combined_text = "\n\n---\n\n".join(relevant_texts)
        
        synthesis_prompt = f"""Ești un asistent juridic. Sintetizează informațiile relevante găsite în documente pentru întrebarea utilizatorului.

Întrebare utilizator: {user_query}

Informații găsite în documente:
{combined_text}

Task: Creează un rezumat concis și precis al informațiilor relevante pentru întrebare. Dacă informațiile nu sunt relevante sau nu răspund la întrebare, returnează DOAR "NU_SUNT_RELEVANTE".

Rezumat:"""
        
        response = llm.invoke(synthesis_prompt)
        result = response.content.strip()
        
        if result.upper() == "NU_SUNT_RELEVANTE" or len(result) < 50:
            return None
        
        return result
        
    except Exception as e:
        if verbose:
            print(f"   ⚠️  Eroare la căutarea în JSON: {e}")
        return None


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


def process_query(user_message: str, conversation_history: list = None, verbose: bool = False, refresh_token: str = None, username: str = None) -> str:
    """
    Procesează un query și returnează rezultatul formatat.
    
    Această funcție poate fi apelată programatic (ex: din frontend).
    
    Args:
        user_message: Mesajul pentru căutare
        conversation_history: Listă de mesaje anterioare din conversație (opțional)
                           Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        verbose: Dacă True, afișează print-uri (default: False pentru API calls)
        refresh_token: Refresh token OAuth pentru Gmail (opțional, pentru trimitere email ANPC)
        username: Username-ul utilizatorului curent (opțional, pentru a obține email-ul din baza de date)
        
    Returns:
        Output-ul formatat ca string
    """
    if verbose:
        print("=" * 70)
        print("🚀 CivicAid - Main Script")
        print("=" * 70)
        print(f"\n📝 Mesaj primit: \"{user_message}\"\n")
    
    # Step 0: Verifică dacă este cerere de formular ANPC
    try:
        from app.tools.anpc_form import generate_anpc_form
        
        form_result = generate_anpc_form(
            user_message=user_message,
            conversation_history=conversation_history,
            refresh_token=refresh_token,
            username=username,
            verbose=verbose
        )
        
        if form_result.get('is_form_request'):
            if form_result.get('needs_info'):
                return form_result['message']  # Mesaj unic cu toate cerințele
            else:
                return form_result['message']  # Confirmare trimitere sau eroare
    except Exception as e:
        if verbose:
            print(f"⚠️  Eroare la verificarea formularului ANPC: {e}")
        # Continuă cu procesarea normală dacă există eroare
    
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
        summary = summarize_results(results, user_message, conversation_history=conversation_history, verbose=verbose)
        if verbose:
            print("✅ Rezumat generat!\n")
    
    # Step 4: Verifică relevanța rezumatului
    api_key = os.getenv("OPENAI_API_KEY")
    if summary and api_key:
        is_relevant = is_summary_relevant(summary, user_message, api_key)
        
        if not is_relevant:
            # Rezumatul nu este relevant - caută în vectorii JSON ca fallback
            if verbose:
                print("\n⚠️  Rezumatul nu este suficient de relevant. Căutare în vectorii JSON...")
            
            json_result = search_in_json_files(user_message, api_key, verbose=verbose)
            
            if json_result:
                # Am găsit informații relevante în vectorii JSON
                summary = json_result
                if verbose:
                    print("✅ Informații relevante găsite în vectorii JSON!\n")
            else:
                # Nu s-au găsit informații relevante nici în vectorii JSON
                if verbose:
                    print("❌ Nu s-au găsit informații relevante nici în vectorii JSON.\n")
                return "❌ Nu mai am informații relevante pentru această întrebare. Te rog să reformulezi întrebarea sau să oferi mai multe detalii."
    
    # Step 4b: Dacă nu există rezumat sau dacă rezumatul este gol, încercă vectorii JSON
    if (not summary or len(summary.strip()) < 50) and api_key:
        if verbose:
            print("\n⚠️  Nu există rezumat sau rezumatul este prea scurt. Căutare în vectorii JSON...")
        
        json_result = search_in_json_files(user_message, api_key, verbose=verbose)
        
        if json_result:
            # Am găsit informații relevante în vectorii JSON
            summary = json_result
            if verbose:
                print("✅ Informații relevante găsite în vectorii JSON!\n")
        else:
            # Nu s-au găsit informații relevante nici în vectorii JSON
            if verbose:
                print("❌ Nu s-au găsit informații relevante nici în vectorii JSON.\n")
            return "❌ Nu mai am informații relevante pentru această întrebare. Te rog să reformulezi întrebarea sau să oferi mai multe detalii."
    
    # Step 5: Combină output-ul detaliat cu rezumatul
    final_output = ""
    if summary:
        final_output = summary
    else:
        final_output = output
    
    # Step 6: Scrie outputul în fișier (doar pentru CLI, nu pentru API)
    # Comentat pentru optimizare - nu este necesar pentru API calls
    # write_output_to_file(final_output, OUTPUT_FILE)
    
    return final_output


# Note: main() function moved to root main.py for CLI entry point


