# 🔎 find_law.py - Găsire Articole de Lege Relevante

## Descriere

Scriptul `find_law.py` permite găsirea articolelor de lege relevante pe baza unui mesaj simplu și informal.

### Funcționalități

1. **Primește mesaje informale** - Poți scrie în limbaj simplu, fără termeni juridici formali
2. **Optimizează query-ul** - Folosește AI pentru a transforma mesajul într-un query optimizat pentru căutare
3. **Caută semantic** - Folosește căutare semantică în vector store pentru a găsi articolele relevante
4. **Afișează rezultate** - Returnează articolele de lege relevante cu sursa și conținutul complet

## Utilizare

### Mod 1: Interactiv (Recomandat pentru prima utilizare)

```bash
python3 scripts/find_law.py
```

Scriptul va întreba:
```
Introdu mesajul tău (ex: 'Am avut un accident de mașină'):
> 
```

### Mod 2: CLI (Rapid pentru testare)

```bash
python3 scripts/find_law.py "Am avut un accident de mașină"
```

## Exemple

### Exemplu 1: Accident de mașină
```bash
python3 scripts/find_law.py "Am avut un accident de mașină"
```

**Output așteptat:**
- Query optimizat: "accident rutier, răspundere civilă, daune materiale"
- Articole relevante din legile despre răspundere civilă, asigurări auto, etc.

### Exemplu 2: Drepturi cetățenești
```bash
python3 scripts/find_law.py "Ce drepturi am ca cetățean?"
```

**Output așteptat:**
- Articole din Constituție despre drepturile fundamentale
- Articole despre cetățenie

### Exemplu 3: Ajutor social
```bash
python3 scripts/find_law.py "Vreau ajutor social pentru că nu am bani"
```

**Output așteptat:**
- Articole despre venit minim garantat
- Articole despre asistență socială
- Articole despre eligibilitate

## Cerințe

1. **Vector store creat** - Trebuie să rulezi mai întâi:
   ```bash
   python3 scripts/ingest_laws.py
   ```

2. **API Key OpenAI** - Trebuie să ai `OPENAI_API_KEY` în fișierul `.env`

3. **PDF-uri indexate** - Trebuie să ai PDF-uri cu legi în `data/raw_laws/`

## Output

Scriptul afișează:
- Mesajul primit
- Query-ul optimizat (dacă optimizarea este activată)
- Articolele de lege relevante cu:
  - Sursa (numele fișierului PDF)
  - Articolul (dacă este identificat)
  - Conținutul complet al articolului

Rezultatele sunt de asemenea salvate în `data/search_results.txt` pentru referință ulterioară.

## Parametri (în cod)

Poți modifica în script:
- `k=5` - Numărul de rezultate returnate (default: 5)
- `use_optimization=True` - Dacă să optimizeze query-ul (default: True)
- `model="gpt-4o-mini"` - Modelul folosit pentru optimizare (default: gpt-4o-mini, rapid și ieftin)

## Troubleshooting

### Eroare: "Vector store nu există"
**Soluție:** Rulează mai întâi `python3 scripts/ingest_laws.py`

### Eroare: "OPENAI_API_KEY nu este setată"
**Soluție:** Creează fișierul `.env` cu `OPENAI_API_KEY=sk-proj-...`

### Nu găsește rezultate relevante
**Cauze posibile:**
- PDF-urile nu conțin informații relevante pentru mesajul tău
- Vector store-ul nu a fost actualizat după adăugarea de PDF-uri noi
- Mesajul este prea specific sau prea general

**Soluție:** 
- Verifică ce PDF-uri ai în `data/raw_laws/`
- Rulează din nou `ingest_laws.py` pentru a reindexa
- Încearcă să reformulezi mesajul

