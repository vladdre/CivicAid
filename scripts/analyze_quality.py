"""
Script pentru analiza calității rezultatelor căutării semantice.

Verifică dacă rezultatele returnate sunt relevante pentru query-urile date.
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


def analyze_query_quality(query, expected_keywords, k=3):
    """Analizează calitatea rezultatelor pentru un query."""
    print(f'\n{"="*70}')
    print(f'QUERY: "{query}"')
    print(f'Cuvinte cheie așteptate: {expected_keywords}')
    print("="*70)
    
    vector_store = Chroma(
        persist_directory=str(VECTOR_STORE_DIR),
        embedding_function=OpenAIEmbeddings(model='text-embedding-3-small'),
        collection_name='civicaid_laws'
    )
    
    results = vector_store.similarity_search(query, k=k)
    
    for i, doc in enumerate(results, 1):
        content_lower = doc.page_content.lower()
        
        # Verifică câte cuvinte cheie sunt prezente
        found = [kw for kw in expected_keywords if kw.lower() in content_lower]
        relevance_score = len(found) / len(expected_keywords) * 100
        
        status = "✓ BUN" if relevance_score >= 50 else "⚠ SLAB" if relevance_score >= 25 else "✗ NERELEVANT"
        
        print(f'\n{i}. {status} (Relevanță: {relevance_score:.0f}% - găsite: {found})')
        print(f'   Sursă: {doc.metadata.get("source")}')
        print(f'   Text: {doc.page_content[:300]}...')
        print('-'*70)
    
    return results


def main():
    print("="*70)
    print("ANALIZĂ CALITATE REZULTATE - Vector Store CivicAid")
    print("="*70)
    
    # Test 1: Drepturi fundamentale - ar trebui să fie foarte relevante
    analyze_query_quality(
        "Ce drepturi fundamentale am ca cetățean?",
        ["drepturi", "fundamental", "cetățean", "articol"]
    )
    
    # Test 2: Separarea puterilor - verifică dacă găsește articolul 1
    analyze_query_quality(
        "Cum funcționează separarea puterilor în stat?",
        ["separat", "puter", "legislativ", "executiv", "judecător", "articolul 1"]
    )
    
    # Test 3: Cetățenie
    analyze_query_quality(
        "Cum obțin cetățenia română?",
        ["cetățenie", "român", "dobândit", "articolul 5"]
    )
    
    # Test 4: Căutare directă pentru articolul 1
    print(f'\n{"="*70}')
    print("CĂUTARE MANUALĂ: ARTICOLUL 1 (Statul român)")
    print("="*70)
    
    vector_store = Chroma(
        persist_directory=str(VECTOR_STORE_DIR),
        embedding_function=OpenAIEmbeddings(model='text-embedding-3-small'),
        collection_name='civicaid_laws'
    )
    
    all_docs = vector_store.similarity_search('', k=200)
    found_art1 = False
    
    for doc in all_docs:
        if 'ARTICOLUL 1:' in doc.page_content or ('ARTICOLUL 1' in doc.page_content and 'Statul român' in doc.page_content):
            print('\n✓ GĂSIT ARTICOLUL 1!')
            print(doc.page_content[:600])
            if 'separat' in doc.page_content.lower() or 'puter' in doc.page_content.lower():
                print('\n✓ CONȚINE SEPARAREA PUTERILOR!')
            found_art1 = True
            break
    
    if not found_art1:
        print('\n✗ Articolul 1 nu a fost găsit în chunks')
        print('\nPrimele chunks pentru referință:')
        for i, doc in enumerate(all_docs[:3], 1):
            print(f'\n{i}. {doc.page_content[:200]}...')
    
    print(f'\n{"="*70}')
    print("ANALIZĂ COMPLETĂ")
    print("="*70)


if __name__ == "__main__":
    main()

