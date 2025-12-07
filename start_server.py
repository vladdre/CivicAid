"""
Script de start pentru CivicAID Server.

Acest script:
1. Verifică și creează vector store dacă nu există (rulează ingest_laws.py)
2. Verifică și creează baza de date SQL dacă nu există (rulează setup_sql_db.py)
3. Pornește serverul Flask

Usage:
    python start_server.py
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))

# Paths
VECTOR_STORE_DIR = PROJECT_ROOT / "data" / "vector_store"
RAW_LAWS_DIR = PROJECT_ROOT / "data" / "raw_laws"
SQL_DB_FILE = PROJECT_ROOT / "data" / "institutions.db"
INSTITUTIONS_JSON = PROJECT_ROOT / "data" / "institutions.json"


def check_vector_store() -> bool:
    """Verifică dacă vector store-ul există și are conținut."""
    if not VECTOR_STORE_DIR.exists():
        return False
    
    try:
        files = list(VECTOR_STORE_DIR.iterdir())
        if len(files) == 0:
            return False
        
        # Verifică dacă există fișiere relevante ChromaDB
        has_content = any(
            f.is_file() and (f.suffix in ['.sqlite', '.db'] or f.name.startswith('chroma'))
            or f.is_dir()
            for f in files
        )
        return has_content
    except Exception:
        return False


def check_sql_database() -> bool:
    """Verifică dacă baza de date SQL există."""
    return SQL_DB_FILE.exists() and SQL_DB_FILE.stat().st_size > 0


def check_pdfs_exist() -> bool:
    """Verifică dacă există PDF-uri în data/raw_laws."""
    if not RAW_LAWS_DIR.exists():
        return False
    
    pdf_files = list(RAW_LAWS_DIR.glob("*.pdf"))
    return len(pdf_files) > 0


def run_ingest_laws():
    """Rulează ingest_laws.py pentru a crea vector store."""
    print("\n" + "=" * 70)
    print("📚 Creare Vector Store")
    print("=" * 70)
    
    if not check_pdfs_exist():
        print("\n⚠️  Nu există PDF-uri în data/raw_laws/")
        print("   Adaugă PDF-uri cu legi în data/raw_laws/ pentru a crea vector store.")
        print("   Continuăm fără vector store (unele funcții nu vor funcționa).\n")
        return False
    
    try:
        # Import și rulează ingest_laws
        from app.scripts.ingest_laws import main as ingest_main
        ingest_main()
        return True
    except Exception as e:
        print(f"\n❌ Eroare la crearea vector store-ului: {e}")
        print("   Continuăm fără vector store (unele funcții nu vor funcționa).\n")
        return False


def run_setup_sql_db():
    """Rulează setup_sql_db.py pentru a crea baza de date SQL."""
    print("\n" + "=" * 70)
    print("🗄️  Creare Baza de Date SQL")
    print("=" * 70)
    
    if not INSTITUTIONS_JSON.exists():
        print("\n⚠️  Nu există data/institutions.json")
        print("   Baza de date SQL nu poate fi creată.")
        print("   Continuăm fără baza de date SQL (căutarea instituțiilor nu va funcționa).\n")
        return False
    
    try:
        # Import și rulează setup_sql_db
        from app.scripts.setup_sql_db import main as setup_main
        setup_main()
        return True
    except Exception as e:
        print(f"\n❌ Eroare la crearea bazei de date SQL: {e}")
        print("   Continuăm fără baza de date SQL (căutarea instituțiilor nu va funcționa).\n")
        return False


def start_flask_server():
    """Pornește serverul Flask."""
    print("\n" + "=" * 70)
    print("🚀 Pornire Server Flask")
    print("=" * 70)
    print("\n✅ Serverul pornește la http://localhost:5000")
    print("   Apasă Ctrl+C pentru a opri serverul\n")
    print("=" * 70)
    print()
    
    try:
        from app.frontend.app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n👋 Server oprit.")
    except Exception as e:
        print(f"\n❌ Eroare la pornirea serverului: {e}")
        sys.exit(1)


def main():
    """Funcția principală de start."""
    print("=" * 70)
    print("🚀 CivicAID - Server Setup & Start")
    print("=" * 70)
    
    # Verifică API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  ATENȚIE: OPENAI_API_KEY nu este setată în .env")
        print("   Unele funcții nu vor funcționa fără API key.\n")
    
    # Step 1: Verifică și creează vector store
    print("\n📋 Verificare Vector Store...")
    if not check_vector_store():
        print("   ⚠️  Vector store nu există sau este gol.")
        print("   🚀 Pornesc crearea vector store-ului...")
        run_ingest_laws()
    else:
        print("   ✅ Vector store există și are conținut.")
    
    # Step 2: Verifică și creează baza de date SQL
    print("\n📋 Verificare Baza de Date SQL...")
    if not check_sql_database():
        print("   ⚠️  Baza de date SQL nu există.")
        print("   🚀 Pornesc crearea bazei de date...")
        run_setup_sql_db()
    else:
        print("   ✅ Baza de date SQL există.")
    
    # Step 3: Pornește serverul Flask
    start_flask_server()


if __name__ == "__main__":
    main()

