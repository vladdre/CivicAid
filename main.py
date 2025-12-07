"""
Entry point pentru CivicAid CLI.

Usage:
    python main.py "Am avut un accident de mașină"
"""

import sys
from app.core.query_processor import process_query

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 70)
        print("❌ Eroare: Mesajul este obligatoriu")
        print("=" * 70)
        print("\nUsage:")
        print("  python main.py \"Mesajul tău pentru căutare\"")
        print("\nExemplu:")
        print("  python main.py \"Am avut un accident de mașină\"")
        sys.exit(1)
    
    # Extrage mesajul din argumente
    user_message = " ".join(sys.argv[1:])
    
    # Procesează query-ul cu verbose=True pentru CLI
    final_output = process_query(user_message, verbose=True)
    
    # Afișează outputul în consolă
    print("\n" + "=" * 70)
    print("📋 Output Final:")
    print("=" * 70)
    print(final_output)
    
    print("\n" + "=" * 70)
    print("✅ Proces completat!")
    print("=" * 70)
