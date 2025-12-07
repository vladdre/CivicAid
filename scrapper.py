#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper Monitor Oficial - Tracking Modificări Legi
Descarcă documentele în ordine descrescătoare și identifică ultima mențiune a fiecărei legi
"""

import requests
import os
import re
import json
from pathlib import Path
import PyPDF2
from typing import Dict, Set, Optional, Tuple

# Configurare
OUTPUT_PDF_DIR = "mo_pdf"
OUTPUT_TEXT_DIR = "mo_text"
OUTPUT_JSON = "legi_tracking.json"
CHECKPOINT_FILE = "checkpoint.json"

# Intervale
YEAR_START = 2025
YEAR_END = 1989

# maximul de modif in MO intr un an
NUM_START = 2000
NUM_END = 1

# Pattern-uri pentru identificare legi (cu număr și an)
LAW_PATTERNS = [
    # Legii [nume] nr. X/YYYY (genitiv cu nume, ex: "Legii petrolului nr. 238/2004")
    r'Legii\s+[a-zăâîșț]+\s+nr\.?\s*(\d+)\s*/\s*(\d{4})',
    # Legea nr. X/YYYY
    r'Legea\s+nr\.?\s*(\d+)\s*/\s*(\d{4})',
    # Legii nr. X/YYYY (genitiv simplu)
    r'Legii\s+nr\.?\s*(\d+)\s*/\s*(\d{4})',
    # OUG nr. X/YYYY
    r'OUG\s+nr\.?\s*(\d+)\s*/\s*(\d{4})',
    r'Ordonanță\s+de\s+urgență\s+nr\.?\s*(\d+)\s*/\s*(\d{4})',
    # HG nr. X/YYYY
    r'Hotărâre\s+a\s+Guvernului\s+nr\.?\s*(\d+)\s*/\s*(\d{4})',
    r'HG\s+nr\.?\s*(\d+)\s*/\s*(\d{4})',
]

# Pattern pentru a detecta modificări explicite
MODIFICATION_KEYWORDS = [
    r'modificarea\s+(?:și\s+)?completarea',
    r'completarea\s+(?:și\s+)?modificarea',
    r'modifică\s+(?:și\s+)?completează',
    r'completează\s+(?:și\s+)?modifică',
    r'abrogă',
    r'abrogare',
    r'se\s+modifică',
    r'se\s+completează',
    r'se\s+abrogă',
]

class MonitorOficialScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://monitoruloficial.ro/",
        })
        
        # Tracking legi: { "Legea_123_2020": { "tip": "Legea", "numar": 123, "an": 2020, 
        #                                       "ultima_mentiune": {...} } }
        self.legi_tracking: Dict[str, Dict] = {}
        
        # Set pentru a evita procesarea dublă
        self.processed_docs: Set[str] = set()
        
        # Creează directoarele
        os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)
        os.makedirs(OUTPUT_TEXT_DIR, exist_ok=True)
        
    def load_checkpoint(self):
        """Încarcă progresul salvat"""
        if os.path.exists(CHECKPOINT_FILE):
            try:
                with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.legi_tracking = data.get('legi_tracking', {})
                    self.processed_docs = set(data.get('processed_docs', []))
                    print(f"Checkpoint încărcat: {len(self.processed_docs)} documente procesate")
            except Exception as e:
                print(f"Eroare la încărcarea checkpoint: {e}")
    
    def save_checkpoint(self):
        """Salvează progresul"""
        try:
            with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'legi_tracking': self.legi_tracking,
                    'processed_docs': list(self.processed_docs)
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Eroare la salvare checkpoint: {e}")
    
    def save_final_json(self):
        """Salvează rezultatul final în JSON"""
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(self.legi_tracking, f, ensure_ascii=False, indent=2)
        print(f"\nRezultat final salvat în {OUTPUT_JSON}")
        print(f"Total legi identificate: {len(self.legi_tracking)}")
    
    def build_url(self, num: int, year: int) -> str:
        """Construiește URL-ul pentru un document"""
        return f"https://monitoruloficial.ro/Monitorul-Oficial--PI--{num}--{year}.html"
    
    def document_exists(self, num: int, year: int) -> bool:
        """Verifică dacă documentul există pe server (folosește HEAD request)"""
        url = self.build_url(num, year)
        try:
            # Folosește HEAD request cu timeout mai scurt pentru documente care nu există
            r = self.session.head(url, allow_redirects=False, timeout=5)
            
            if r.status_code != 200:
                return False
            
            # Verifică Content-Type - trebuie să fie PDF
            content_type = r.headers.get('Content-Type', '').lower()
            if 'pdf' not in content_type:
                return False
            
            # Verifică dimensiunea - PDF-urile valide au cel puțin câteva KB
            content_length = r.headers.get('Content-Length')
            if content_length:
                size = int(content_length)
                if size < 1000:  # Mai mic de 1KB probabil nu e PDF valid
                    return False
            
            return True
        except Exception as e:
            # În caz de eroare sau timeout, considerăm că nu există
            return False
    
    def download_pdf(self, num: int, year: int) -> Optional[bytes]:
        """Descarcă PDF-ul pentru un document"""
        url = self.build_url(num, year)
        fname = f"{year}_{num}.pdf"
        filepath = os.path.join(OUTPUT_PDF_DIR, fname)
        
        # Verifică dacă fișierul există deja
        if os.path.exists(filepath):
            print(f"  PDF există deja: {fname}")
            try:
                with open(filepath, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"  Eroare la citirea PDF existent: {e}")
                return None
        
        # Verifică dacă documentul există pe server înainte de descărcare
        if not self.document_exists(num, year):
            # Documentul nu există, nu mai încercăm să-l descărcăm
            return None
        
        try:
            r = self.session.get(url, allow_redirects=False, timeout=30)
            if r.status_code == 200:
                print(f"  PDF descărcat: {fname} ({len(r.content)} bytes)")
                # Salvează PDF-ul
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                return r.content
            elif r.status_code == 404:
                # Documentul nu există
                return None
            else:
                print(f"  Eroare HTTP {r.status_code} pentru {fname}")
                return None
        except Exception as e:
            print(f"  Eroare la descărcare {fname}: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> Optional[str]:
        """Extrage textul din PDF"""
        try:
            from io import BytesIO
            pdf_file = BytesIO(pdf_content)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"    Eroare la extragere text PDF: {e}")
            return None
    
    def find_laws_in_text(self, text: str, doc_id: str) -> Set[tuple]:
        """
        Identifică toate legile menționate în text
        Returnează set de tuple: (tip, numar, an) sau (tip, None, None) pentru coduri
        """
        laws_found = set()
        
        # Caută pattern-uri cu număr și an
        for pattern in LAW_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                numar = match.group(1)
                an = match.group(2)
                # Determină tipul
                if 'OUG' in match.group(0) or 'Ordonanță' in match.group(0):
                    tip = "OUG"
                elif 'Hotărâre' in match.group(0) or 'HG' in match.group(0):
                    tip = "HG"
                elif 'Legii' in match.group(0):
                    tip = "Legea"  # Normalizăm genitivul
                else:
                    tip = "Legea"
                laws_found.add((tip, int(numar), int(an)))
        
        # Caută coduri (fără număr)
        cod_patterns = {
            r'Codul\s+de\s+procedură\s+penală': 'Codul de procedură penală',
            r'Codul\s+de\s+procedură\s+civilă': 'Codul de procedură civilă',
            r'Codul\s+penal': 'Codul penal',
            r'Codul\s+civil': 'Codul civil',
        }
        for pattern, cod_name in cod_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                laws_found.add((cod_name, None, None))
        
        return laws_found
    
    def extract_law_context(self, text: str, law_mention: str, context_size: int = 5000) -> Tuple[str, bool]:
        """
        Extrage contextul complet al legii din text
        Returnează: (text_context, is_modification)
        """
        # Caută toate mențiunile legii în text
        mention_positions = []
        search_text = text
        start_pos = 0
        
        while True:
            pos = search_text.find(law_mention, start_pos)
            if pos == -1:
                break
            mention_positions.append(pos)
            start_pos = pos + len(law_mention)
        
        if not mention_positions:
            return "", False
        
        # Folosește prima mențiune pentru a extrage contextul
        mention_pos = mention_positions[0]
        
        # Extrage context extins (context_size caractere înainte și după)
        start = max(0, mention_pos - context_size)
        end = min(len(text), mention_pos + len(law_mention) + context_size)
        context = text[start:end]
        
        # Verifică dacă este modificare
        is_modification = False
        for keyword_pattern in MODIFICATION_KEYWORDS:
            if re.search(keyword_pattern, context, re.IGNORECASE):
                is_modification = True
                break
        
        return context.strip(), is_modification
    
    def is_modification_context(self, text: str, law_mention: str) -> bool:
        """Verifică dacă mențiunea legii este în context de modificare"""
        _, is_mod = self.extract_law_context(text, law_mention, context_size=1000)
        return is_mod
    
    def process_document(self, num: int, year: int):
        """Procesează un document: descarcă, extrage text, identifică legi"""
        doc_id = f"{year}_{num}"
        
        # Verifică dacă a fost deja procesat
        if doc_id in self.processed_docs:
            return
        
        print(f"\nProcesare: {doc_id}")
        
        # Descarcă PDF
        pdf_content = self.download_pdf(num, year)
        if pdf_content is None:
            return
        
        # Extrage text
        text = self.extract_text_from_pdf(pdf_content)
        if text is None or len(text.strip()) < 100:
            print(f"  Text prea scurt sau inexistent pentru {doc_id}")
            return
        
        # Salvează text (opțional, pentru debugging)
        text_file = os.path.join(OUTPUT_TEXT_DIR, f"{doc_id}.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Identifică legi
        laws_found = self.find_laws_in_text(text, doc_id)
        
        print(f"  Legi identificate: {len(laws_found)}")
        
        # Actualizează tracking (ordine descrescătoare = ultima mențiune)
        for law_info in laws_found:
            tip, numar, an = law_info
            
            # Creează cheia unică
            if numar is not None and an is not None:
                key = f"{tip}_{numar}_{an}"
            else:
                # Pentru coduri, folosim numele
                key = f"Cod_{tip.replace(' ', '_')}"
            
            # Extrage contextul complet al legii și verifică dacă este modificare
            # Caută mențiunea exactă în text
            if numar is not None and an is not None:
                mention_pattern = f"{tip} nr. {numar}/{an}"
            else:
                mention_pattern = tip
            
            # Extrage textul complet al legii (context extins)
            law_text, is_modification = self.extract_law_context(text, mention_pattern, context_size=5000)
            
            # Actualizează tracking (doar dacă nu există sau dacă documentul curent e mai nou)
            if key not in self.legi_tracking:
                # Prima mențiune a legii
                self.legi_tracking[key] = {
                    "tip": tip,
                    "numar": numar,
                    "an": an,
                    "ultima_mentiune": {
                        "document": f"{doc_id}.pdf",
                        "an_document": year,
                        "nr_document": num,
                        "este_modificare": is_modification,
                        "text_lege": law_text  # Textul complet al legii
                    },
                    "ultima_modificare": None  # Inițializare
                }
                
                # Dacă este modificare, setează ultima_modificare
                if is_modification:
                    self.legi_tracking[key]["ultima_modificare"] = {
                        "document": f"{doc_id}.pdf",
                        "an_document": year,
                        "nr_document": num,
                        "text_lege": law_text  # Textul complet al modificării
                    }
            else:
                # Verifică dacă documentul curent e mai nou pentru ultima_mentiune
                existing_mentiune = self.legi_tracking[key]["ultima_mentiune"]
                if (year > existing_mentiune["an_document"]) or \
                   (year == existing_mentiune["an_document"] and num > existing_mentiune["nr_document"]):
                    self.legi_tracking[key]["ultima_mentiune"] = {
                        "document": f"{doc_id}.pdf",
                        "an_document": year,
                        "nr_document": num,
                        "este_modificare": is_modification,
                        "text_lege": law_text  # Textul complet al legii
                    }
                
                # Actualizează ultima_modificare dacă este modificare și documentul e mai nou
                if is_modification:
                    existing_modificare = self.legi_tracking[key]["ultima_modificare"]
                    if existing_modificare is None:
                        # Prima modificare găsită
                        self.legi_tracking[key]["ultima_modificare"] = {
                            "document": f"{doc_id}.pdf",
                            "an_document": year,
                            "nr_document": num,
                            "text_lege": law_text  # Textul complet al modificării
                        }
                    else:
                        # Verifică dacă documentul curent e mai nou decât ultima modificare
                        if (year > existing_modificare["an_document"]) or \
                           (year == existing_modificare["an_document"] and num > existing_modificare["nr_document"]):
                            self.legi_tracking[key]["ultima_modificare"] = {
                                "document": f"{doc_id}.pdf",
                                "an_document": year,
                                "nr_document": num,
                                "text_lege": law_text  # Textul complet al modificării
                            }
        
        # Marchează ca procesat
        self.processed_docs.add(doc_id)
        
        # Salvează checkpoint la fiecare 10 documente
        if len(self.processed_docs) % 10 == 0:
            self.save_checkpoint()
            print(f"  Checkpoint salvat ({len(self.processed_docs)} documente procesate)")
    
    def find_first_existing_document(self, year: int) -> Optional[int]:
        """
        Folosește binary search pentru a găsi primul document care există (cel mai mare număr)
        Returnează numărul primului document existent sau None dacă nu există niciunul
        """
        left = NUM_END
        right = NUM_START
        first_existing = None
        
        print(f"  Căutare binary search pentru primul document existent în {year}...")
        
        while left <= right:
            mid = (left + right) // 2
            
            if self.document_exists(mid, year):
                # Documentul există, deci toate mai mici vor exista
                first_existing = mid
                # Caută mai sus pentru a găsi cel mai mare număr care există
                left = mid + 1
            else:
                # Documentul nu există, caută mai jos
                right = mid - 1
        
        if first_existing:
            print(f"  ✓ Primul document existent în {year}: {first_existing}")
        else:
            print(f"  ✗ Nu există documente în {year}")
        
        return first_existing
    
    def run(self):
        """Rulează scraper-ul"""
        print("=" * 60)
        print("Scraper Monitor Oficial - Tracking Modificări Legi")
        print("=" * 60)
        print(f"Ani: {YEAR_START} → {YEAR_END}")
        print(f"Numere: {NUM_START} → {NUM_END}")
        print(f"Ordine: DESCENDENTĂ (cel mai nou primul)")
        print("Strategie: Binary search pentru primul document existent")
        print("=" * 60)
        
        # Încarcă checkpoint
        self.load_checkpoint()
        
        total_docs = 0
        docs_found = 0
        last_checkpoint_save = len(self.processed_docs)  # Ultima dată când s-a salvat checkpoint
        
        try:
            # Iterează prin ani (descrescător)
            for year in range(YEAR_START, YEAR_END - 1, -1):
                print(f"\n{'='*60}")
                print(f"An: {year}")
                print(f"{'='*60}")
                
                # Folosește binary search pentru a găsi primul document existent
                first_existing = self.find_first_existing_document(year)
                
                if first_existing is None:
                    print(f"  Nu există documente în {year}, trec la următorul an")
                    continue
                
                # Procesează toate documentele de la primul existent până la NUM_END
                # (toate mai mici decât primul vor exista)
                for num in range(first_existing, NUM_END - 1, -1):
                    total_docs += 1
                    
                    # Procesează documentul (nu mai verificăm existența, știm că există)
                    self.process_document(num, year)
                    
                    # Verifică dacă documentul a fost procesat
                    doc_id = f"{year}_{num}"
                    if doc_id in self.processed_docs:
                        docs_found += 1
                    
                    # Salvează checkpoint la fiecare 10 documente procesate
                    current_processed = len(self.processed_docs)
                    if current_processed - last_checkpoint_save >= 10:
                        self.save_checkpoint()
                        last_checkpoint_save = current_processed
                        print(f"  Checkpoint salvat ({current_processed} procesate)")
                    
                    # Pauză mică pentru a nu suprasolicita serverul
                    import time
                    time.sleep(0.5)
        
        except KeyboardInterrupt:
            print("\n\nScraper întrerupt de utilizator")
        except Exception as e:
            print(f"\n\nEroare: {e}")
        finally:
            # Salvează progresul final
            self.save_checkpoint()
            self.save_final_json()
            
            print(f"\n{'='*60}")
            print("Statistici finale:")
            print(f"  Documente verificate: {total_docs}")
            print(f"  Documente găsite: {docs_found}")
            print(f"  Legi identificate: {len(self.legi_tracking)}")
            print(f"{'='*60}")


if __name__ == "__main__":
    scraper = MonitorOficialScraper()
    scraper.run()

