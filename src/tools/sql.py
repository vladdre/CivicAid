"""
Tool pentru interogare baza de date SQL folosind Text-to-SQL.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI

load_dotenv()
sys.path.append(str(Path(__file__).parent.parent.parent))

BASE_DIR = Path(__file__).parent.parent.parent
DB_FILE = BASE_DIR / "data" / "institutions.db"
TEMP_FILE = BASE_DIR / ".temp"
TMP_FILE = BASE_DIR / ".tmp"
OUTPUT_DIR = BASE_DIR / "data"


def get_api_key():
    """Obține cheia API OpenAI din .temp, .tmp sau .env."""
    # Încearcă .temp mai întâi
    for temp_file in [TEMP_FILE, TMP_FILE]:
        if temp_file.exists():
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('OPENAI_API_KEY=') and not line.startswith('#'):
                            key = line.split('=', 1)[1].strip()
                            if key and key != 'sk-proj-your-api-key-here':
                                return key
                        # Dacă linia nu are '=', poate fi doar cheia direct
                        elif line and not line.startswith('#') and line.startswith('sk-'):
                            return line.strip()
            except Exception:
                pass
    return os.getenv("OPENAI_API_KEY")


def get_sql_database():
    """Creează și returnează un obiect SQLDatabase conectat la baza de date."""
    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"Baza de date nu există: {DB_FILE}\n"
            f"Rulează mai întâi: python scripts/setup_sql_db.py"
        )
    db_url = f"sqlite:///{DB_FILE}"
    return SQLDatabase.from_uri(db_url)


def save_results_to_file(query: str, results: str, sql_query: str = None) -> str:
    """
    Salvează rezultatele în fișierul output.txt din directorul data.
    
    Mai întâi apelează main.py pentru a obține rezultatele din vector store,
    apoi adaugă rezultatele SQL la fișier.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "output.txt"
    
    # Step 1: Apelează main.py pentru a obține rezultatele din vector store
    main_output = ""
    try:
        import subprocess
        import sys
        
        # Rulează main.py cu query-ul
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "main.py"), query],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR),
            timeout=300  # Timeout de 5 minute
        )
        
        if result.returncode == 0:
            # Citește output-ul generat de main.py
            main_output_file = BASE_DIR / "output.txt"
            if main_output_file.exists():
                with open(main_output_file, 'r', encoding='utf-8') as f:
                    main_output = f.read()
        else:
            # Dacă main.py a eșuat, continuă fără rezultatele din vector store
            print(f"⚠️  main.py a returnat cod {result.returncode}: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  main.py a depășit timeout-ul")
    except Exception as e:
        print(f"⚠️  Eroare la rularea main.py: {e}")
    
    # Step 2: Combină output-ul din main.py cu rezultatele SQL
    combined_output = ""
    
    if main_output:
        combined_output = main_output
        combined_output += "\n\n" + "=" * 70 + "\n"
        combined_output += "📍 REZULTATE INSTITUȚII (SQL)\n"
        combined_output += "=" * 70 + "\n\n"
    else:
        combined_output = "=" * 70 + "\n"
        combined_output += "📍 REZULTATE INSTITUȚII (SQL)\n"
        combined_output += "=" * 70 + "\n\n"
    
    combined_output += results
    
    # Step 3: Scrie în fișierul din data/
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_output)
    
    return str(output_file)


def query_institutions(natural_language_query: str) -> str:
    """
    Transformă o întrebare în limbaj natural într-un query SQL.
    
    Caută direct în baza de date folosind cuvintele din întrebare.
    Salvează rezultatele într-un fișier în directorul data.
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("OPENAI_API_KEY nu este setată în .temp sau .env")
    
    try:
        db = get_sql_database()
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key)
        schema = db.get_table_info()
        
        # Prompt simplu - caută direct cuvintele din întrebare în baza de date
        prompt = f"""Ești un expert SQL. Generează un query SQL pentru următoarea întrebare.

Schema bazei de date:
{schema}

INSTRUCȚIUNI SIMPLE:
1. Extrage cuvintele cheie din întrebare (ex: "accident", "pensie", "buletin")
2. Caută aceste cuvinte în coloanele 'nume' și 'tip_serviciu' folosind LIKE '%cuvânt%'
3. Folosește OR pentru a combina căutările în ambele coloane
4. Returnează DOAR: nume, adresa, program

EXEMPLE:
- "accident" → SELECT nume, adresa, program FROM institutions WHERE tip_serviciu LIKE '%accident%' OR nume LIKE '%accident%' OR nume LIKE '%Rutieră%'
- "pensie" → SELECT nume, adresa, program FROM institutions WHERE nume LIKE '%pensie%' OR tip_serviciu LIKE '%pensie%'
- "buletin" → SELECT nume, adresa, program FROM institutions WHERE tip_serviciu LIKE '%identitate%' OR tip_serviciu LIKE '%buletin%' OR nume LIKE '%Evidență%'
- "energie" → SELECT nume, adresa, program FROM institutions WHERE tip_serviciu LIKE '%energie%' OR tip_serviciu LIKE '%căldură%' OR tip_serviciu LIKE '%gaz%'

Întrebare: {natural_language_query}

Generează DOAR query-ul SQL, fără explicații, fără markdown, fără backticks.
Query SQL:"""
        
        response = llm.invoke(prompt)
        sql_query = response.content.strip()
        
        # Curăță SQL-ul
        if sql_query.startswith("```"):
            sql_query = sql_query.split("```")[1]
            if sql_query.startswith("sql"):
                sql_query = sql_query[3:]
            sql_query = sql_query.strip()
        
        # Execută query-ul
        result = db.run(sql_query)
        
        if not result or result.strip() == "":
            formatted_result = "Nu am găsit instituții care să corespundă cerințelor tale."
        else:
            formatted_result = format_sql_results(result)
        
        # Salvează rezultatele în fișier
        output_file = save_results_to_file(natural_language_query, formatted_result, sql_query)
        
        # Returnează doar rezultatul formatat (fără mesajul despre fișier)
        return formatted_result
        
    except Exception as e:
        error_msg = f"❌ Eroare: {str(e)}"
        # Salvează și eroarea în fișier
        try:
            save_results_to_file(natural_language_query, error_msg)
        except:
            pass
        return error_msg


def format_sql_results(result: str) -> str:
    """Formatează rezultatele SQL."""
    import ast
    
    try:
        cleaned = result.strip()
        if cleaned.startswith('[') or cleaned.startswith('('):
            parsed = ast.literal_eval(cleaned)
        else:
            return result
        
        if not parsed:
            return "Nu am găsit instituții care să corespundă cerințelor tale."
        
        formatted = []
        for i, row in enumerate(parsed, 1):
            if isinstance(row, (list, tuple)):
                if len(row) >= 5:
                    nume = str(row[1]) if len(row) > 1 else "N/A"
                    adresa = str(row[2]) if len(row) > 2 else "N/A"
                    program = str(row[4]) if len(row) > 4 else "N/A"
                elif len(row) == 1:
                    nume = "N/A"
                    adresa = "N/A"
                    program = str(row[0])
                else:
                    nume = str(row[0]) if len(row) > 0 else "N/A"
                    adresa = str(row[1]) if len(row) > 1 else "N/A"
                    program = str(row[2]) if len(row) > 2 else "N/A"
            else:
                nume = "N/A"
                adresa = "N/A"
                program = str(row)
            
            formatted.append(
                f"{i}. {nume}\n"
                f"   📍 {adresa}\n"
                f"   🕐 {program}"
            )
        
        return "\n\n".join(formatted)
        
    except:
        return result
