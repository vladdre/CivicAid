"""
Script de diagnostic pentru a verifica cum funcționează embeddings-urile și căutarea.

Acest script ajută la identificarea problemelor cu relevanța rezultatelor.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

VECTOR_STORE_DIR = Path(__file__).parent.parent / "data" / "vector_store"
COLLECTION_NAME = "civicaid_laws"


def check_embeddings_consistency():
    """Verifică dacă același model de embeddings este folosit."""
    print("=" * 70)
    print("🔍 Diagnostic Embeddings și Vector Store")
    print("=" * 70)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY nu este setată")
        return
    
    # Modelul folosit la creare (din ingest_laws.py)
    embedding_model = "text-embedding-3-small"
    print(f"\n📊 Model de embeddings folosit: {embedding_model}")
    
    if not VECTOR_STORE_DIR.exists():
        print(f"\n❌ Vector store nu există la: {VECTOR_STORE_DIR}")
        print("   Rulează: python scripts/ingest_laws.py")
        return
    
    # Încarcă vector store-ul cu ACELAȘI model
    print(f"\n📂 Încărcare vector store din: {VECTOR_STORE_DIR}")
    embeddings = OpenAIEmbeddings(
        model=embedding_model,
        openai_api_key=api_key
    )
    
    try:
        vector_store = Chroma(
            persist_directory=str(VECTOR_STORE_DIR),
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
        print("✓ Vector store încărcat")
    except Exception as e:
        print(f"❌ Eroare la încărcare: {e}")
        return
    
    # Verifică conținutul
    print("\n📚 Verificare conținut vector store:")
    try:
        # Obține câteva documente pentru a vedea ce conțin
        sample_docs = vector_store.similarity_search("", k=5)
        print(f"   • Total chunks disponibile: {len(sample_docs)}")
        
        if sample_docs:
            print("\n   📄 Exemple de conținut:")
            for i, doc in enumerate(sample_docs[:3], 1):
                source = doc.metadata.get("source", "Necunoscut")
                content_preview = doc.page_content[:150].replace("\n", " ")
                print(f"   {i}. [{source}]")
                print(f"      {content_preview}...")
    except Exception as e:
        print(f"   ⚠️  Eroare: {e}")
    
    # Testează căutarea cu query simplu
    print("\n🔍 Test căutare semantică:")
    test_queries = [
        "accident",
        "accident de mașină",
        "răspundere civilă",
        "daune"
    ]
    
    for query in test_queries:
        print(f"\n   Query: \"{query}\"")
        try:
            results = vector_store.similarity_search(query, k=2)
            if results:
                for i, doc in enumerate(results, 1):
                    source = doc.metadata.get("source", "Necunoscut")
                    score = getattr(doc, 'score', 'N/A')
                    content_preview = doc.page_content[:100].replace("\n", " ")
                    print(f"      {i}. [{source}] Score: {score}")
                    print(f"         {content_preview}...")
            else:
                print("      ⚠️  Nu s-au găsit rezultate")
        except Exception as e:
            print(f"      ❌ Eroare: {e}")
    
    # Verifică dacă embeddings-urile sunt create corect
    print("\n🔢 Test creare embeddings:")
    try:
        test_text = "accident de mașină"
        embedding_vector = embeddings.embed_query(test_text)
        print(f"   ✓ Embedding creat pentru \"{test_text}\"")
        print(f"   • Dimensiune vector: {len(embedding_vector)}")
        print(f"   • Primele 5 valori: {embedding_vector[:5]}")
    except Exception as e:
        print(f"   ❌ Eroare la creare embedding: {e}")
    
    print("\n" + "=" * 70)
    print("✅ Diagnostic completat")
    print("=" * 70)


if __name__ == "__main__":
    check_embeddings_consistency()

