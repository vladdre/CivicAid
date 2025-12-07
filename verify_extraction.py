#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de verificare extragere legi și text
"""

import json
import os
from scrapper import MonitorOficialScraper

def verify_law_extraction():
    """Verifică extragerea legilor și textului"""
    
    scraper = MonitorOficialScraper()
    
    # Procesează documentele de test
    print("=" * 80)
    print("VERIFICARE EXTREGERE LEGI ȘI TEXT")
    print("=" * 80)
    
    # Procesează documentele
    for num in [1127, 1126, 1125]:
        scraper.process_document(num, 2025)
    
    # Salvează rezultatul
    scraper.save_final_json()
    
    # Analizează rezultatele
    print("\n" + "=" * 80)
    print("ANALIZĂ REZULTATE")
    print("=" * 80)
    
    with open('legi_tracking.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    legi_cu_text = 0
    legi_fara_text = 0
    legi_cu_modificare = 0
    
    print(f"\nTotal legi identificate: {len(data)}\n")
    
    for lege_id, lege_info in data.items():
        ultima_mentiune = lege_info.get('ultima_mentiune', {})
        text_lege = ultima_mentiune.get('text_lege', '')
        
        if text_lege:
            legi_cu_text += 1
            text_length = len(text_lege)
            este_modificare = ultima_mentiune.get('este_modificare', False)
            
            if este_modificare:
                legi_cu_modificare += 1
            
            print(f"\n{'='*80}")
            print(f"LEGE: {lege_id}")
            print(f"  Tip: {lege_info.get('tip')} nr. {lege_info.get('numar')}/{lege_info.get('an')}")
            print(f"  Document: {ultima_mentiune.get('document')}")
            print(f"  Este modificare: {este_modificare}")
            print(f"  Lungime text: {text_length} caractere")
            print(f"  Preview text (primele 500 caractere):")
            print(f"  {'-'*80}")
            print(f"  {text_lege[:500]}...")
            print(f"  {'-'*80}")
            
            # Verifică dacă are ultima_modificare
            ultima_modificare = lege_info.get('ultima_modificare')
            if ultima_modificare:
                print(f"  Ultima modificare:")
                print(f"    Document: {ultima_modificare.get('document')}")
                mod_text = ultima_modificare.get('text_lege', '')
                if mod_text:
                    print(f"    Text modificare (primele 300 caractere):")
                    print(f"    {mod_text[:300]}...")
        else:
            legi_fara_text += 1
            print(f"\n⚠️  {lege_id}: FĂRĂ TEXT")
    
    print("\n" + "=" * 80)
    print("STATISTICI")
    print("=" * 80)
    print(f"Legi cu text extras: {legi_cu_text}")
    print(f"Legi fără text: {legi_fara_text}")
    print(f"Legi cu modificare: {legi_cu_modificare}")
    if len(data) > 0:
        print(f"Procentaj cu text: {legi_cu_text/len(data)*100:.1f}%")

if __name__ == "__main__":
    verify_law_extraction()

