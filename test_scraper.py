#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pentru verificarea funcționalității scraper-ului
pe documentul existent
"""

import os
import re
from scrapper import MonitorOficialScraper

def test_on_existing_document():
    """Testează scraper-ul pe documentul existent"""
    scraper = MonitorOficialScraper()
    
    # Test pe documentul 2025_1127
    pdf_path = "Monitorul Oficial Partea I nr. 1127.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Documentul {pdf_path} nu există!")
        return
    
    print("Testare pe documentul existent...")
    print(f"Fișier: {pdf_path}\n")
    
    # Citește PDF
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Extrage text
    text = scraper.extract_text_from_pdf(pdf_content)
    if text:
        print(f"Text extras: {len(text)} caractere\n")
        
        # Identifică legi
        laws_found = scraper.find_laws_in_text(text, "2025_1127")
        print(f"Legi identificate: {len(laws_found)}")
        for law in sorted(laws_found):
            print(f"  - {law}")
        
        # Verifică pattern-uri specifice
        print("\n" + "="*60)
        print("Verificare pattern-uri specifice:")
        print("="*60)
        
        test_patterns = [
            (r'Legea\s+nr\.?\s*263\s*/\s*2010', "Legea nr. 263/2010"),
            (r'Legii\s+petrolului\s+nr\.?\s*238\s*/\s*2004', "Legii petrolului nr. 238/2004"),
            (r'Codul\s+de\s+procedură\s+penală', "Codul de procedură penală"),
            (r'Legea\s+nr\.?\s*303\s*/\s*2022', "Legea nr. 303/2022"),
        ]
        
        for pattern, name in test_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"✓ Găsit: {name}")
            else:
                print(f"✗ Nu găsit: {name}")
    else:
        print("Nu s-a putut extrage textul din PDF!")

if __name__ == "__main__":
    test_on_existing_document()

