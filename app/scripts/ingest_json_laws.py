"""
Data Ingestion Pipeline for CivicAid RAG System - JSON Laws

This script creates a separate vector store from legi.json:
1. Load: Loads legi.json and extracts text from each law
2. Split: Chunks documents using RecursiveCharacterTextSplitter
3. Embed: Creates embeddings using OpenAIEmbeddings
4. Store: Saves vectors to ChromaDB at data/vector_store_json

Usage:
    python -m app.scripts.ingest_json_laws
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "app"))

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

# Configuration
LEGI_JSON = PROJECT_ROOT / "legi.json"
VECTOR_STORE_JSON_DIR = PROJECT_ROOT / "data" / "vector_store_json"

# Chunking parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def load_json_laws(legi_json_path: Path) -> list:
    """
    Încarcă legile din fișierul JSON și creează Document objects.
    
    Args:
        legi_json_path: Path către fișierul legi.json
        
    Returns:
        Lista de Document objects
    """
    if not legi_json_path.exists():
        print(f"❌ Fișierul {legi_json_path} nu există.")
        return []
    
    print(f"\n📖 Încărcare legi din {legi_json_path.name}...")
    
    try:
        with open(legi_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Eroare la citirea JSON: {e}")
        return []
    except Exception as e:
        print(f"❌ Eroare neașteptată: {e}")
        return []
    
    documents = []
    
    for law_key, law_data in data.items():
        # Extrage informații despre lege
        tip = law_data.get('tip', 'Legea')
        numar = law_data.get('numar', 'N/A')
        an = law_data.get('an', 'N/A')
        
        # Construiește identificatorul legii
        law_id = f"{tip} nr. {numar}/{an}"
        
        # Extrage textul din ultima_mentiune
        ultima_mentiune = law_data.get('ultima_mentiune', {})
        text_mentiune = ultima_mentiune.get('text_lege', '')
        
        # Extrage textul din ultima_modificare (dacă există)
        ultima_modificare = law_data.get('ultima_modificare')
        text_modificare = ''
        if ultima_modificare and isinstance(ultima_modificare, dict):
            text_modificare = ultima_modificare.get('text_lege', '')
        
        # Combină textele (prioritizează modificarea dacă există)
        combined_text = text_modificare if text_modificare else text_mentiune
        
        # Skip dacă nu există text
        if not combined_text or len(combined_text.strip()) < 50:
            continue
        
        # Creează Document cu metadata
        doc = Document(
            page_content=combined_text,
            metadata={
                'source': f'legi.json',
                'law_id': law_id,
                'law_key': law_key,
                'tip': tip,
                'numar': numar,
                'an': an,
                'has_modification': bool(text_modificare)
            }
        )
        documents.append(doc)
    
    print(f"  ✓ Încărcat {len(documents)} legi din JSON")
    return documents


def split_documents(documents: list, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list:
    """
    Împarte documentele în chunks mai mici.
    
    Args:
        documents: Lista de Document objects
        chunk_size: Dimensiunea maximă a unui chunk
        chunk_overlap: Suprapunerea între chunks
        
    Returns:
        Lista de chunks (Document objects)
    """
    if not documents:
        return []
    
    print(f"\n✂️  Împărțire documente în chunks...")
    print(f"   Chunk size: {chunk_size}, Overlap: {chunk_overlap}")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = []
    for doc in documents:
        doc_chunks = text_splitter.split_documents([doc])
        # Păstrează metadata din documentul original
        for chunk in doc_chunks:
            chunk.metadata.update(doc.metadata)
        chunks.extend(doc_chunks)
    
    print(f"  ✓ Creat {len(chunks)} chunks din {len(documents)} documente")
    
    return chunks


def create_vector_store(chunks: list, vector_store_dir: Path) -> Chroma:
    """
    Creează embeddings și le salvează în ChromaDB.
    
    Args:
        chunks: Lista de chunked Document objects
        vector_store_dir: Directorul unde va fi salvat ChromaDB
        
    Returns:
        Chroma vector store instance
    """
    if not chunks:
        print("⚠️  Nu există chunks pentru embedding. Omit crearea vector store.")
        return None
    
    # Verifică OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY nu este setată în variabilele de mediu. "
            "Te rog să o setezi în fișierul .env."
        )
    
    print(f"\n🔢 Creare embeddings folosind OpenAI...")
    
    # Inițializează embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",  # Model eficient din punct de vedere al costurilor
        openai_api_key=api_key
    )
    
    print(f"💾 Salvare vectori în ChromaDB la {vector_store_dir}...")
    
    # Creează sau încarcă vector store
    # Dacă vector_store_dir există, va încărca datele existente
    # Altfel, va crea un store nou
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(vector_store_dir),
        collection_name="civicaid_json_laws"  # Colecție separată pentru JSON
    )
    
    print(f"  ✓ Total documente indexate: {len(chunks)}")
    
    return vector_store


def main():
    """
    Execuție principală a pipeline-ului ETL.
    """
    print("=" * 60)
    print("🚀 CivicAid - JSON Laws Ingestion Pipeline")
    print("=" * 60)
    
    # Step 1: Încarcă legile din JSON
    documents = load_json_laws(LEGI_JSON)
    
    if not documents:
        print("\n❌ Nu există documente de procesat. Ieșire.")
        return
    
    # Step 2: Împarte în chunks
    chunks = split_documents(documents)
    
    if not chunks:
        print("\n❌ Nu s-au creat chunks. Ieșire.")
        return
    
    # Step 3: Creează embeddings și salvează în ChromaDB
    try:
        vector_store = create_vector_store(chunks, VECTOR_STORE_JSON_DIR)
        
        if vector_store:
            print("\n" + "=" * 60)
            print("✅ Pipeline-ul de ingestie a fost finalizat cu succes!")
            print("=" * 60)
            print(f"\n📊 Rezumat:")
            print(f"   • Legi procesate: {len(documents)}")
            print(f"   • Total chunks: {len(chunks)}")
            print(f"   • Locație vector store: {VECTOR_STORE_JSON_DIR}")
            print(f"\n💡 Acum poți folosi vector store-ul JSON în sistemul RAG!")
            
    except Exception as e:
        print(f"\n❌ Eroare la crearea vector store-ului: {str(e)}")
        print(f"   Asigură-te că OPENAI_API_KEY este setată în fișierul .env.")
        sys.exit(1)


if __name__ == "__main__":
    main()

