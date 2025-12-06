"""
Tool pentru interogare baza de date SQL folosind Text-to-SQL.

Acest tool permite agentului să transforme întrebări în limbaj natural
în query-uri SQL și să obțină informații despre instituții.

Exemplu:
    query = "Unde depun cererea pentru pensie?"
    result = query_institutions(query)
    # Returnează: lista de instituții care oferă servicii legate de pensie
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
DB_FILE = BASE_DIR / "data" / "institutions.db"
TEMP_FILE = BASE_DIR / ".temp"


def get_api_key():
    """
    Obține cheia API OpenAI din .temp sau .env.
    Verifică mai întâi .temp, apoi .env.
    
    Returns:
        str: Cheia API sau None dacă nu este găsită
    """
    # Verifică mai întâi .temp
    if TEMP_FILE.exists():
        try:
            with open(TEMP_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENAI_API_KEY=') and not line.startswith('#'):
                        key = line.split('=', 1)[1].strip()
                        if key and key != 'sk-proj-your-api-key-here':
                            return key
        except Exception:
            pass
    
    # Dacă nu este în .temp, verifică .env
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    return None


def get_sql_database():
    """
    Creează și returnează un obiect SQLDatabase conectat la baza de date.
    
    Returns:
        SQLDatabase: Obiect pentru interogare baza de date
    """
    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"Baza de date nu există: {DB_FILE}\n"
            f"Rulează mai întâi: python scripts/setup_sql_db.py"
        )
    
    db_url = f"sqlite:///{DB_FILE}"
    return SQLDatabase.from_uri(db_url)


def query_institutions(natural_language_query: str) -> str:
    """
    Transformă o întrebare în limbaj natural într-un query SQL și returnează rezultatele.
    
    Această funcție folosește LangChain SQL Agent pentru a genera SQL din natural language
    și pentru a executa query-ul pe baza de date.
    
    Args:
        natural_language_query: Întrebarea utilizatorului în limbaj natural
                               (ex: "Unde depun cererea pentru pensie?")
    
    Returns:
        str: Rezultatele interogării formatate pentru utilizator
        
    Example:
        >>> result = query_institutions("Unde găsesc servicii de asistență socială în sectorul 1?")
        >>> print(result)
        "Găsiți următoarele instituții:
        - DGASPC Sector 1: Str. Amzei nr. 10, Sector 1, București
          Program: Luni-Joi 08:00-16:00, Vineri 08:00-14:00
          Servicii: Asistență Socială, Alocații, Handicap, Protecție Copil"
    """
    # Verifică API key
    api_key = get_api_key()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY nu este setată în .temp sau .env\n"
            "Adaugă cheia ta OpenAI în fișierul .temp sau .env"
        )
    
    try:
        # Conectează la baza de date
        db = get_sql_database()
        
        # Creează LLM pentru generarea SQL
        llm = ChatOpenAI(
            model="gpt-4o-mini",  # Model mai ieftin pentru SQL generation
            temperature=0,  # Temperature 0 pentru SQL precis
            openai_api_key=api_key
        )
        
        # Generează SQL direct folosind LLM-ul cu schema bazei de date
        schema = db.get_table_info()
        
        prompt = f"""Ești un expert SQL. Analizează întrebarea și generează un query SQL precis.

Schema bazei de date:
{schema}

REGULI CRITICE:
1. Analizează INTENȚIA întrebării, nu doar cuvintele
2. Caută în AMBELE coloane: 'nume' ȘI 'tip_serviciu'
3. Folosește LIKE '%text%' pentru căutări parțiale (case-insensitive)
4. Folosește OR pentru a combina mai multe condiții
5. Returnează DOAR: nume, adresa, program

MAPARE INTELIGENTĂ ÎNTREBĂRI → INSTITUȚII:
- "pensie" / "pensia" / "pensii" → Casa Națională de Pensii (caută 'Pensii' în nume)
- "handicap" / "dizabilități" / "certificat handicap" → Oficiul pentru Persoane cu Dizabilități SAU DGASPC cu 'Handicap' în tip_serviciu
- "buletin" / "acte identitate" / "identitate" / "carte identitate" → Direcția de Evidență a Persoanelor SAU Primării (caută 'identitate' SAU 'Evidență' în tip_serviciu/nume)
- "pașaport" → Direcția de Evidență a Persoanelor (caută 'pașaport' SAU 'Evidență' în tip_serviciu/nume)
- "șomaj" / "alocație șomaj" → ANOFM (caută 'șomaj' SAU 'ANOFM' SAU 'ocupare' în tip_serviciu/nume)
- "alocații" / "alocație copil" → DGASPC (caută 'Alocații' în tip_serviciu)
- "firmă" / "înregistrare firmă" / "PFA" / "SRL" → Registrul Comerțului (caută 'Registrul Comerțului' în nume)
- "accident" / "urgență" / "spital" → NU este în baza de date, returnează query gol SAU nu returnează nimic
- "fiscal" / "certificat fiscal" / "ANAF" → ANAF (caută 'ANAF' SAU 'fiscal' în nume/tip_serviciu)
- "imigrări" / "vize" / "ședere" → Oficiul pentru Imigrări (caută 'Imigrări' SAU 'vize' în nume/tip_serviciu)

ATENȚIE: Dacă întrebarea nu se referă la instituții din baza de date (ex: "accident", "spital", "poliție"), returnează un query care nu găsește nimic SAU un mesaj clar.

EXEMPLE CORECTE:
- "unde depun pensia": SELECT nume, adresa, program FROM institutions WHERE nume LIKE '%Pensii%'
- "buletin": SELECT nume, adresa, program FROM institutions WHERE tip_serviciu LIKE '%identitate%' OR tip_serviciu LIKE '%Evidență%' OR nume LIKE '%Evidență%'
- "pensia de handicap": SELECT nume, adresa, program FROM institutions WHERE (nume LIKE '%Pensii%' OR tip_serviciu LIKE '%pensie%') AND (tip_serviciu LIKE '%Handicap%' OR nume LIKE '%Dizabilități%')

Întrebare: {natural_language_query}

Generează DOAR query-ul SQL, fără explicații, fără markdown, fără backticks. Folosește tabelul 'institutions'.
Query SQL:"""
        
        # Generează SQL-ul folosind LLM-ul
        response = llm.invoke(prompt)
        sql_query = response.content.strip()
        
        # Curăță SQL-ul (elimină markdown code blocks dacă există)
        if sql_query.startswith("```"):
            sql_query = sql_query.split("```")[1]
            if sql_query.startswith("sql"):
                sql_query = sql_query[3:]
            sql_query = sql_query.strip()
        
        # Execută SQL query-ul
        result = db.run(sql_query)
        
        # Formatează rezultatul
        if not result or result.strip() == "":
            return "Nu am găsit instituții care să corespundă cerințelor tale."
        
        # Parsează rezultatul și formatează frumos
        # Rezultatul vine ca string cu tuple-uri sau lista
        formatted_result = format_sql_results(result)
        
        return formatted_result
        
    except FileNotFoundError as e:
        return f"❌ Eroare: {str(e)}"
    except Exception as e:
        return f"❌ Eroare la interogarea bazei de date: {str(e)}"


def query_institutions_simple(natural_language_query: str) -> str:
    """
    Versiune simplificată care folosește direct SQLDatabase.run() pentru query-uri simple.
    
    Această funcție este mai rapidă pentru query-uri directe, dar nu are capacitatea
    de reasoning a agentului complet.
    
    Args:
        natural_language_query: Întrebarea utilizatorului
        
    Returns:
        str: Rezultatele interogării
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("OPENAI_API_KEY nu este setată în .temp sau .env")
    
    try:
        db = get_sql_database()
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=api_key
        )
        
        # Folosește metoda directă pentru query-uri simple
        result = db.run(natural_language_query)
        
        return result
        
    except Exception as e:
        return f"❌ Eroare: {str(e)}"


def format_sql_results(result: str) -> str:
    """
    Formatează rezultatele SQL într-un format frumos și ușor de citit.
    
    Args:
        result: Rezultatul SQL ca string (poate conține tuple-uri sau liste)
        
    Returns:
        str: Text formatat cu nume, adresă și program
    """
    import ast
    import re
    
    # Încearcă să parseze rezultatul ca Python literal (tuple-uri/liste)
    try:
        # Curăță string-ul și încearcă să-l parseze
        cleaned = result.strip()
        if cleaned.startswith('[') or cleaned.startswith('('):
            parsed = ast.literal_eval(cleaned)
        else:
            # Dacă nu e listă/tuple, încearcă să extragă datele manual
            return format_raw_sql_result(result)
        
        if not parsed:
            return "Nu am găsit instituții care să corespundă cerințelor tale."
        
        formatted = []
        for i, row in enumerate(parsed, 1):
            if isinstance(row, (list, tuple)):
                # Determină ce coloane avem în funcție de numărul de elemente
                if len(row) >= 5:
                    # Format complet: (id, nume, adresa, tip_serviciu, program, grad_ocupare)
                    nume = str(row[1]) if len(row) > 1 else "N/A"
                    adresa = str(row[2]) if len(row) > 2 else "N/A"
                    program = str(row[4]) if len(row) > 4 else "N/A"
                elif len(row) == 1:
                    # Doar o coloană (ex: doar programul)
                    nume = "N/A"
                    adresa = "N/A"
                    program = str(row[0])
                else:
                    # Format parțial
                    nume = str(row[0]) if len(row) > 0 else "N/A"
                    adresa = str(row[1]) if len(row) > 1 else "N/A"
                    program = str(row[2]) if len(row) > 2 else "N/A"
            else:
                # Dacă nu e tuple/listă, folosește direct valoarea
                nume = "N/A"
                adresa = "N/A"
                program = str(row)
            
            formatted.append(
                f"{i}. {nume}\n"
                f"   📍 {adresa}\n"
                f"   🕐 {program}"
            )
        
        return "\n\n".join(formatted)
        
    except (ValueError, SyntaxError, AttributeError):
        # Dacă nu poate parsa, returnează formatat manual
        return format_raw_sql_result(result)


def format_raw_sql_result(result: str) -> str:
    """
    Formatează rezultatul SQL când nu poate fi parsat ca Python literal.
    """
    # Extrage informații folosind regex
    lines = result.split('\n')
    formatted = []
    
    for i, line in enumerate(lines, 1):
        if line.strip() and not line.strip().startswith('(') and not line.strip().startswith('['):
            formatted.append(f"{i}. {line.strip()}")
    
    return "\n".join(formatted) if formatted else result


def format_institution_results(results: list) -> str:
    """
    Formatează rezultatele interogării într-un format prietenos pentru utilizator.
    
    Args:
        results: Lista de dicționare cu rezultatele interogării
        
    Returns:
        str: Text formatat
    """
    if not results:
        return "Nu am găsit instituții care să corespundă cerințelor tale."
    
    formatted = []
    for i, inst in enumerate(results, 1):
        formatted.append(
            f"{i}. **{inst.get('nume', 'N/A')}**\n"
            f"   📍 Adresă: {inst.get('adresa', 'N/A')}\n"
            f"   🕐 Program: {inst.get('program', 'N/A')}\n"
            f"   📋 Servicii: {inst.get('tip_serviciu', 'N/A')}\n"
            f"   👥 Grad ocupare: {inst.get('grad_ocupare', 'N/A')}"
        )
    
    return "\n\n".join(formatted)


# Funcție helper pentru testare
def test_sql_tool():
    """
    Funcție de test pentru verificarea funcționalității tool-ului SQL.
    """
    print("=" * 60)
    print("🧪 Test SQL Tool - CivicAid")
    print("=" * 60)
    
    test_queries = [
        "Unde depun cererea pentru pensie?",
        "Care instituții oferă servicii de asistență socială în sectorul 1?",
        "Unde găsesc servicii pentru handicap?",
        "Care este programul de lucru al DGASPC Sector 4?",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        try:
            result = query_institutions(query)
            print(f"✅ Rezultat:\n{result}")
        except Exception as e:
            print(f"❌ Eroare: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test completat!")
    print("=" * 60)


if __name__ == "__main__":
    # Rulează testele dacă scriptul este executat direct
    test_sql_tool()

