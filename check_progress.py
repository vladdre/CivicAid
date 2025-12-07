#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pentru verificare progres scraper
"""

import json
import os
from datetime import datetime

def check_progress():
    print("=" * 80)
    print("VERIFICARE PROGRES SCRAPER")
    print("=" * 80)
    print(f"Timp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Verifică checkpoint
    if os.path.exists('checkpoint.json'):
        with open('checkpoint.json', 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        processed = len(checkpoint.get('processed_docs', []))
        legi = len(checkpoint.get('legi_tracking', {}))
        
        print(f"✓ Checkpoint găsit")
        print(f"  Documente procesate: {processed}")
        print(f"  Legi identificate: {legi}")
        
        # Ultimele documente procesate
        docs = checkpoint.get('processed_docs', [])
        if docs:
            print(f"\n  Ultimul document procesat: {docs[-1]}")
            print(f"\n  Ultimele 10 documente procesate:")
            for doc in docs[-10:]:
                print(f"    - {doc}")
            
            # Analiză progres
            if len(docs) > 1:
                # Extrage an și număr din ultimul document
                last_doc = docs[-1]
                try:
                    year, num = last_doc.split('_')
                    year = int(year)
                    num = int(num)
                    print(f"\n  Progres:")
                    print(f"    An curent: {year}")
                    print(f"    Număr curent: {num}")
                    print(f"    Ani rămași: {year - 1989}")
                    if year == 2025:
                        print(f"    Numere rămase în anul {year}: {num - 1}")
                    
                    # Estimat timp rămas (aproximativ)
                    total_ani = 2025 - 1989 + 1
                    ani_procesati = 2025 - year + 1
                    if ani_procesati > 0:
                        procent = (ani_procesati / total_ani) * 100
                        print(f"    Progres estimat: {procent:.1f}%")
                except:
                    pass
    else:
        print("⚠️  Checkpoint nu există încă")
        print("  (Se creează după primele 10 documente procesate)")
    
    # Verifică PDF-uri
    if os.path.exists('mo_pdf'):
        pdf_files = [f for f in os.listdir('mo_pdf') if f.endswith('.pdf')]
        pdf_count = len(pdf_files)
        print(f"\n  PDF-uri descărcate: {pdf_count}")
        
        # Ultimul PDF descărcat (după nume)
        if pdf_files:
            pdf_files_sorted = sorted(pdf_files, reverse=True)
            print(f"  Ultimul PDF descărcat: {pdf_files_sorted[0]}")
    else:
        print(f"\n  PDF-uri descărcate: 0")
    
    # Verifică fișier final
    if os.path.exists('legi_tracking.json'):
        size = os.path.getsize('legi_tracking.json')
        print(f"  legi_tracking.json: {size/1024:.1f} KB")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_progress()

