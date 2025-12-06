#!/usr/bin/env python3
"""
Script interactiv pentru testarea bazei de date locale.
Permite să pui întrebări direct fără server.

Usage:
    python test_db.py
    python test_db.py "Unde depun cererea pentru pensie?"
"""

import sys
from pathlib import Path

# Add parent directory to path (tests -> CivicAid root)
sys.path.append(str(Path(__file__).parent.parent))

from src.tools.sql import query_institutions, get_sql_database, get_api_key


def test_single_query(query: str):
    """Testează o singură întrebare."""
    print("=" * 70)
    print(f"📝 Întrebare: {query}")
    print("=" * 70)
    
    try:
        result = query_institutions(query)
        print(f"\n✅ Răspuns:\n{result}\n")
        print(f"💾 Rezultatul a fost salvat în: data/output.txt")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Eroare: {e}\n")
        print("=" * 70)


def interactive_mode():
    """Mod interactiv - permite să pui întrebări repetat."""
    print("=" * 70)
    print("🔍 Test Baza de Date Locală - CivicAid")
    print("=" * 70)
    
    # Verifică conexiunea
    db_file = Path(__file__).parent / "data" / "institutions.db"
    if not db_file.exists():
        print(f"❌ Baza de date nu există: {db_file}")
        print(f"   Rulează mai întâi: python scripts/setup_sql_db.py")
        return
    
    api_key = get_api_key()
    if not api_key:
        print("❌ OPENAI_API_KEY nu este setată în .temp sau .env")
        return
    
    print(f"✓ Baza de date: {db_file.name}")
    print(f"✓ API key: configurată\n")
    
    # Testează schema
    try:
        db = get_sql_database()
        result = db.run("SELECT COUNT(*) as total FROM institutions")
        print(f"📊 Total instituții în baza de date: {result}\n")
    except Exception as e:
        print(f"⚠️  Eroare la verificarea bazei de date: {e}\n")
    
    print("💡 Introdu întrebările despre instituții (sau 'quit' pentru ieșire)")
    print("-" * 70)
    
    while True:
        try:
            query = input("\n❓ Întrebare: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q', 'iesire']:
                print("\n👋 La revedere!")
                break
            
            test_single_query(query)
            
        except KeyboardInterrupt:
            print("\n\n👋 La revedere!")
            break
        except Exception as e:
            print(f"\n❌ Eroare: {e}\n")


def main():
    """Funcția principală."""
    if len(sys.argv) > 1:
        # Mod CLI - o singură întrebare
        query = " ".join(sys.argv[1:])
        test_single_query(query)
    else:
        # Mod interactiv
        interactive_mode()


if __name__ == "__main__":
    main()

