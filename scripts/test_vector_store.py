"""
Script de test pentru verificarea funcționalității vector store-ului.

Acest script permite testarea explicită a:
1. Încărcării vector store-ului
2. Căutării semantice
3. Verificării metadata-ului
4. Testarea cu diferite query-uri

Usage:
    python scripts/test_vector_store.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

# Configuration
VECTOR_STORE_DIR = Path(__file__).parent.parent / "data" / "vector_store"


def test_vector_store():
    """Testează funcționalitatea vector store-ului."""
    
    print("=" * 60)
    print("🧪 Test Vector Store - CivicAid")
    print("=" * 60)
    
    # Verifică dacă vector store-ul există
    if not VECTOR_STORE_DIR.exists():
        print(f"❌ Vector store nu există la: {VECTOR_STORE_DIR}")
        print("   Rulează mai întâi: python scripts/ingest_laws.py")
        return
    
    # Verifică API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY nu este setată în .env")
        return
    
    print(f"✓ Vector store găsit la: {VECTOR_STORE_DIR}")
    print(f"✓ API key configurată\n")
    
    # Încarcă vector store-ul
    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key
        )
        vector_store = Chroma(
            persist_directory=str(VECTOR_STORE_DIR),
            embedding_function=embeddings,
            collection_name="civicaid_laws"
        )
        print("✓ Vector store încărcat cu succes\n")
    except Exception as e:
        print(f"❌ Eroare la încărcarea vector store-ului: {e}")
        return
    
    # Testează numărul de documente
    try:
        # Obține toate documentele pentru a număra
        all_docs = vector_store.similarity_search("", k=1000)  # Query gol pentru a obține toate
        print(f"📊 Număr total de chunks în vector store: {len(all_docs)}")
        
        # Obține sursele unice
        sources = set(doc.metadata.get("source", "unknown") for doc in all_docs)
        print(f"📚 Surse unice: {len(sources)}")
        for source in sources:
            count = sum(1 for doc in all_docs if doc.metadata.get("source") == source)
            print(f"   • {source}: {count} chunks")
        print()
    except Exception as e:
        print(f"⚠️  Nu s-au putut număra documentele: {e}\n")
    
    # Testează căutări semantice
    test_queries = [
        "drepturi fundamentale",
        "cetățenie română",
        "separarea puterilor",
        "guvernul",
        "parlament"
    ]
    
    print("🔍 Testare căutări semantice:")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n📝 Query: \"{query}\"")
        print("-" * 60)
        
        try:
            results = vector_store.similarity_search(query, k=2)
            
            for i, doc in enumerate(results, 1):
                source = doc.metadata.get("source", "N/A")
                page_content = doc.page_content[:150].replace("\n", " ")
                print(f"  {i}. [{source}]")
                print(f"     {page_content}...")
        
        except Exception as e:
            print(f"  ❌ Eroare: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test completat!")
    print("=" * 60)


if __name__ == "__main__":
    test_vector_store()

