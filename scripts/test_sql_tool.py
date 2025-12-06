"""
Script de test pentru verificarea funcționalității tool-ului SQL.

Acest script testează dacă tool-ul SQL poate transforma întrebări naturale
în query-uri SQL și să returneze rezultate relevante.

Usage:
    python scripts/test_sql_tool.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.tools.sql import query_institutions, get_sql_database, get_api_key

# Load environment variables
load_dotenv()


def test_database_connection():
    """Testează conexiunea la baza de date."""
    print("=" * 60)
    print("🧪 Test SQL Tool - CivicAid")
    print("=" * 60)
    
    # Verifică dacă baza de date există
    db_file = Path(__file__).parent.parent / "data" / "institutions.db"
    if not db_file.exists():
        print(f"❌ Baza de date nu există: {db_file}")
        print(f"   Rulează mai întâi: python scripts/setup_sql_db.py")
        return False
    
    print(f"✓ Baza de date găsită: {db_file.name}")
    
    # Verifică API key (din .temp sau .env)
    api_key = get_api_key()
    if not api_key:
        print("❌ OPENAI_API_KEY nu este setată în .temp sau .env")
        return False
    
    print(f"✓ API key configurată (din .temp sau .env)\n")
    return True


def test_simple_queries():
    """Testează query-uri simple."""
    print("🔍 Testare query-uri simple:")
    print("=" * 60)
    
    test_queries = [
        "Unde depun cererea pentru pensie?",
        "Care instituții oferă servicii de asistență socială în sectorul 1?",
        "Unde găsesc servicii pentru handicap?",
        "Care este programul de lucru al DGASPC Sector 4?",
        "Unde pot obține acte de identitate?",
        "Unde mă înregistrez pentru șomaj?",
        "Care este adresa Casei Naționale de Pensii?",
        "Unde pot obține un pașaport?",
        "Unde depun cererea pentru împrumut studențesc?",
        "Unde găsesc servicii pentru persoane cu dizabilități?",
        "Unde pot plăti facturile prin poștă?",
        "Care instituții oferă servicii fiscale?",
        "Unde pot înregistra o firmă?",
        "Unde găsesc servicii pentru imigrări și vize?",
        "Care este programul de lucru al ANAF?",
        "Unde pot obține un certificat fiscal?",
        "Unde găsesc servicii pentru protecția copilului?",
        "Care instituții oferă alocații?",
        "Unde pot obține un certificat de handicap?",
        "Unde găsesc servicii pentru asigurări de sănătate?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 60)
        try:
            result = query_institutions(query)
            print(f"✅ Rezultat:\n{result}\n")
        except Exception as e:
            print(f"❌ Eroare: {e}\n")
    
    print("=" * 60)


def test_database_schema():
    """Testează dacă schema bazei de date este corectă."""
    print("\n📊 Verificare schema bazei de date:")
    print("=" * 60)
    
    try:
        db = get_sql_database()
        
        # Obține informații despre schema
        table_info = db.get_table_info()
        print("✓ Schema bazei de date:")
        print(table_info)
        
        # Testează un query SQL direct
        print("\n📝 Test query SQL direct:")
        result = db.run("SELECT COUNT(*) as total FROM institutions")
        print(f"✓ Total instituții în baza de date: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Eroare: {e}")
        return False


def main():
    """Funcția principală de test."""
    if not test_database_connection():
        return
    
    if not test_database_schema():
        return
    
    test_simple_queries()
    
    print("\n" + "=" * 60)
    print("✅ Toate testele completate!")
    print("=" * 60)


if __name__ == "__main__":
    main()

