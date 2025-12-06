"""
Script pentru crearea și popularea bazei de date SQLite cu instituții.

Acest script:
1. Citește datele din data/institutions.json
2. Creează tabelul 'institutions' în SQLite
3. Populează baza de date cu datele din JSON

Usage:
    python scripts/setup_sql_db.py
"""

import json
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configuration
BASE_DIR = Path(__file__).parent.parent
JSON_FILE = BASE_DIR / "data" / "institutions.json"
DB_FILE = BASE_DIR / "data" / "institutions.db"

# SQLAlchemy setup
Base = declarative_base()


class Institution(Base):
    """Model SQLAlchemy pentru tabelul institutions."""
    __tablename__ = 'institutions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nume = Column(Text, nullable=False)
    adresa = Column(Text, nullable=False)
    tip_serviciu = Column(Text, nullable=False)
    program = Column(Text, nullable=False)
    grad_ocupare = Column(Text, nullable=True)


def load_institutions_from_json(json_file: Path) -> list:
    """
    Încarcă datele instituțiilor din fișierul JSON.
    
    Args:
        json_file: Path către fișierul JSON
        
    Returns:
        Lista de dicționare cu datele instituțiilor
    """
    if not json_file.exists():
        print(f"❌ Fișierul JSON nu există: {json_file}")
        print(f"   Creează fișierul {json_file} cu datele instituțiilor.")
        return []
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            institutions = json.load(f)
        
        print(f"✓ Încărcat {len(institutions)} instituții din {json_file.name}")
        return institutions
    
    except json.JSONDecodeError as e:
        print(f"❌ Eroare la citirea JSON: {e}")
        return []
    except Exception as e:
        print(f"❌ Eroare neașteptată: {e}")
        return []


def create_database(db_file: Path) -> tuple:
    """
    Creează baza de date SQLite și tabelul institutions.
    
    Args:
        db_file: Path către fișierul bazei de date
        
    Returns:
        Tuple (engine, session)
    """
    # Creează directorul dacă nu există
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Șterge baza de date existentă dacă există (pentru re-creare)
    if db_file.exists():
        print(f"⚠️  Baza de date există deja: {db_file.name}")
        response = input("   Vrei să o ștergi și să o recreezi? (da/nu): ").strip().lower()
        if response in ['da', 'd', 'yes', 'y']:
            db_file.unlink()
            print(f"   ✓ Baza de date veche ștearsă")
        else:
            print(f"   → Păstrăm baza de date existentă")
    
    # Creează engine-ul SQLAlchemy
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, echo=False)
    
    # Creează toate tabelele
    Base.metadata.create_all(engine)
    
    print(f"✓ Baza de date creată: {db_file.name}")
    
    # Creează session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    return engine, session


def populate_database(session, institutions: list):
    """
    Populează baza de date cu datele din JSON.
    
    Args:
        session: SQLAlchemy session
        institutions: Lista de dicționare cu datele instituțiilor
    """
    if not institutions:
        print("⚠️  Nu există instituții de adăugat.")
        return
    
    print(f"\n📝 Adăugare {len(institutions)} instituții în baza de date...")
    
    added_count = 0
    skipped_count = 0
    
    for inst_data in institutions:
        # Verifică dacă instituția există deja (după nume)
        existing = session.query(Institution).filter_by(nume=inst_data['nume']).first()
        
        if existing:
            print(f"  ⚠️  Skip: {inst_data['nume']} (există deja)")
            skipped_count += 1
            continue
        
        # Creează noua instituție
        institution = Institution(
            nume=inst_data['nume'],
            adresa=inst_data['adresa'],
            tip_serviciu=inst_data['tip_serviciu'],
            program=inst_data['program'],
            grad_ocupare=inst_data.get('grad_ocupare', '')
        )
        
        session.add(institution)
        added_count += 1
        print(f"  ✓ Adăugat: {inst_data['nume']}")
    
    # Commit toate modificările
    session.commit()
    
    print(f"\n📊 Rezumat:")
    print(f"   • Instituții adăugate: {added_count}")
    if skipped_count > 0:
        print(f"   • Instituții omise (există deja): {skipped_count}")


def verify_database(session):
    """
    Verifică conținutul bazei de date.
    
    Args:
        session: SQLAlchemy session
    """
    count = session.query(Institution).count()
    print(f"\n✅ Verificare baza de date:")
    print(f"   • Total instituții în baza de date: {count}")
    
    if count > 0:
        print(f"\n   Primele 3 instituții:")
        institutions = session.query(Institution).limit(3).all()
        for inst in institutions:
            print(f"   • {inst.nume} - {inst.adresa}")


def main():
    """
    Funcția principală care execută pipeline-ul complet.
    """
    print("=" * 60)
    print("🚀 CivicAid - Setup SQL Database")
    print("=" * 60)
    
    # Step 1: Încarcă datele din JSON
    institutions = load_institutions_from_json(JSON_FILE)
    
    if not institutions:
        print("\n❌ Nu există date de procesat. Ieșire.")
        return
    
    # Step 2: Creează baza de date
    try:
        engine, session = create_database(DB_FILE)
    except Exception as e:
        print(f"\n❌ Eroare la crearea bazei de date: {e}")
        return
    
    # Step 3: Populează baza de date
    try:
        populate_database(session, institutions)
    except Exception as e:
        print(f"\n❌ Eroare la popularea bazei de date: {e}")
        session.rollback()
        return
    
    # Step 4: Verifică rezultatul
    verify_database(session)
    
    session.close()
    
    print("\n" + "=" * 60)
    print("✅ Setup baza de date completat cu succes!")
    print("=" * 60)
    print(f"\n💡 Baza de date este disponibilă la: {DB_FILE}")
    print(f"   Poți folosi această bază de date în tool-ul SQL (src/tools/sql.py)")


if __name__ == "__main__":
    main()

