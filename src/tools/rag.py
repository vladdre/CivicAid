"""
Tool pentru consultare legislație folosind RAG (Retrieval-Augmented Generation).

Acest tool permite agentului să caute informații în documentele legale procesate
și stocate în vector store (ChromaDB). Folosește căutare semantică pentru a găsi
pasaje relevante din PDF-uri și conținut scraped.

Exemplu:
    query = "Ce drepturi fundamentale am ca cetățean?"
    result = consult_legislation(query, vector_store)
    # Returnează: pasaje relevante din Constituție cu sursa
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

# Configuration
VECTOR_STORE_DIR = Path(__file__).parent.parent.parent / "data" / "vector_store"
COLLECTION_NAME = "civicaid_laws"  # Same collection as ingest_laws.py


def get_vector_store(vector_store_dir: Path = VECTOR_STORE_DIR) -> Optional[Chroma]:
    """
    Încarcă vector store-ul existent.
    
    Args:
        vector_store_dir: Directorul unde este stocat ChromaDB
        
    Returns:
        Chroma vector store instance sau None dacă nu există
    """
    if not vector_store_dir.exists():
        return None
    
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key
        )
        
        vector_store = Chroma(
            persist_directory=str(vector_store_dir),
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
        
        return vector_store
    except Exception as e:
        print(f"Error loading vector store: {e}")
        return None


def consult_legislation(query: str, vector_store: Optional[Chroma] = None, k: int = 3) -> str:
    """
    Consultă legislația folosind RAG (Retrieval-Augmented Generation).
    
    Această funcție caută în vector store-ul cu documente legale (PDF-uri și conținut scraped)
    și returnează pasaje relevante pentru query-ul utilizatorului.
    
    IMPORTANT: Această unealtă trebuie folosită ORI DE CÂTE ORI utilizatorul întreabă
    despre drepturi, legi, proceduri sau eligibilitate. Agentul NU trebuie să răspundă
    din memorie proprie!
    
    Args:
        query: Întrebarea utilizatorului în limbaj natural
              (ex: "Ce drepturi fundamentale am ca cetățean?")
        vector_store: Optional vector store instance. Dacă nu este furnizat,
                     va încărca automat din VECTOR_STORE_DIR
        k: Numărul de pasaje relevante de returnat (default: 3)
    
    Returns:
        str: Pasaje relevante formatate cu sursa, sau mesaj de eroare
        
    Example:
        >>> result = consult_legislation("Ce drepturi fundamentale am?")
        >>> print(result)
        "Sursă: Constitutia-Romaniei.pdf
         Text: TITLUL II - Drepturile, libertatile si îndatoririle fundamentale..."
    """
    # Încarcă vector store dacă nu este furnizat
    if vector_store is None:
        vector_store = get_vector_store()
    
    if vector_store is None:
        return (
            "❌ Nu pot accesa baza de date cu documente legale.\n"
            "   Verifică că:\n"
            "   1. Vector store-ul există (rulează: python scripts/ingest_laws.py)\n"
            "   2. OPENAI_API_KEY este setată în .env"
        )
    
    try:
        # Caută pasaje similare în vector store
        results = vector_store.similarity_search(query, k=k)
        
        if not results:
            return (
                "Nu am găsit informații relevante în documentele legale disponibile.\n"
                "Încearcă să reformulezi întrebarea sau verifică dacă documentele au fost procesate."
            )
        
        # Formatează rezultatele
        formatted_results = []
        
        for i, doc in enumerate(results, 1):
            # Extrage sursa
            source = doc.metadata.get("source", "Document necunoscut")
            url = doc.metadata.get("url", None)
            doc_type = doc.metadata.get("type", "legislation")
            
            # Determină sursa pentru afișare
            if url:
                source_display = f"Web: {url}"
            elif source:
                source_display = f"Document: {source}"
            else:
                source_display = "Sursă necunoscută"
            
            # Extrage textul
            text = doc.page_content.strip()
            
            # Formatează conform specificațiilor: "Sursă: [Nume Doc] \n Text: [Conținut]"
            formatted_results.append(
                f"Sursă: {source_display}\n"
                f"Text: {text}"
            )
        
        # Returnează toate rezultatele
        return "\n\n---\n\n".join(formatted_results)
        
    except Exception as e:
        return f"❌ Eroare la consultarea legislației: {str(e)}"


def consult_legislation_with_metadata(
    query: str, 
    vector_store: Optional[Chroma] = None, 
    k: int = 3
) -> dict:
    """
    Versiune extinsă care returnează și metadata pentru analiză avansată.
    
    Args:
        query: Întrebarea utilizatorului
        vector_store: Optional vector store instance
        k: Numărul de pasaje de returnat
        
    Returns:
        dict: Rezultate cu metadata completă
    """
    if vector_store is None:
        vector_store = get_vector_store()
    
    if vector_store is None:
        return {
            "error": "Vector store nu este disponibil",
            "results": []
        }
    
    try:
        results = vector_store.similarity_search_with_score(query, k=k)
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "source": doc.metadata.get("source", "N/A"),
                "url": doc.metadata.get("url", None),
                "type": doc.metadata.get("type", "legislation"),
                "date": doc.metadata.get("date", None),
                "text": doc.page_content,
                "similarity_score": score
            })
        
        return {
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "results": []
        }


# Funcție helper pentru testare
def test_rag_tool():
    """
    Funcție de test pentru verificarea funcționalității tool-ului RAG.
    """
    print("=" * 60)
    print("🧪 Test RAG Tool - CivicAid")
    print("=" * 60)
    
    # Verifică dacă vector store există
    vector_store = get_vector_store()
    if not vector_store:
        print("❌ Vector store nu este disponibil")
        print("   Rulează mai întâi: python scripts/ingest_laws.py")
        return
    
    print("✓ Vector store încărcat\n")
    
    # Testează cu query-uri reale
    test_queries = [
        "Ce drepturi fundamentale am ca cetățean?",
        "Cum funcționează separarea puterilor?",
        "Care sunt drepturile și obligațiile cetățenilor?",
        "Ce spune Constituția despre cetățenie?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"📝 Test {i}: {query}")
        print("-" * 60)
        try:
            result = consult_legislation(query, vector_store)
            print(f"✅ Rezultat:\n{result}\n")
        except Exception as e:
            print(f"❌ Eroare: {e}\n")
    
    print("=" * 60)
    print("✅ Test completat!")
    print("=" * 60)


if __name__ == "__main__":
    # Rulează testele dacă scriptul este executat direct
    test_rag_tool()

