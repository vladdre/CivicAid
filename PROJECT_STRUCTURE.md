# 📁 CivicAid - Structura Proiectului

Acest document descrie structura completă a proiectului **CivicAid** și rolul fiecărui director/fișier.

## 🌳 Structura Completă

```
VitalLink/
├── .env                          # Variabile de mediu (API keys) - NU se comite în Git!
├── .gitignore                    # Fișiere ignorate de Git
├── requirements.txt              # Dependențele Python
├── README.md                     # Documentația principală
├── TECHNICAL_SPECS.md            # Specificații tehnice detaliate
├── PROJECT_STRUCTURE.md          # Acest fișier
│
├── data/                         # 📦 Toate datele proiectului
│   ├── raw_laws/                 # PDF-uri cu legi (input pentru ingest_laws.py)
│   │   ├── legea_196_2016.pdf
│   │   ├── constitutia.pdf
│   │   └── ...
│   │
│   ├── scraped_content/          # Text brut extras de pe site-uri (backup)
│   │   ├── anunturi_primarie_2024_01_15.txt
│   │   ├── anunturi_dgaspc_2024_01_16.txt
│   │   └── ...
│   │
│   ├── vector_store/              # ChromaDB - Vector store unificat (PDF-uri + Scraping)
│   │   └── (fișiere generate automat de ChromaDB)
│   │
│   └── institutions.db            # SQLite - Baza de date cu instituții
│
├── scripts/                      # 🔧 Scripturi de procesare date
│   ├── __init__.py
│   ├── ingest_laws.py             # ETL: PDF → Chunks → Vector Store
│   ├── scrape_news.py             # ETL: Web Scraping → Text → Vector Store
│   └── setup_sql_db.py            # ETL: Creează și populează SQLite
│
└── src/                           # 💻 Codul sursă al aplicației
    ├── __init__.py
    ├── agent.py                   # Agent orchestrator (creierul)
    ├── prompts.py                 # System prompt și persona
    │
    ├── tools/                     # 🛠️ Uneltele agentului
    │   ├── __init__.py
    │   └── sql.py                 # Tool pentru interogare baza de date (Text-to-SQL)
    │
    └── ui/                        # 🖥️ Interfața utilizator
        ├── __init__.py
        └── app.py                 # Aplicația Streamlit
```

---

## 📂 Explicație Detaliată pe Directoare

### `/data/` - Stocarea Datelor

#### `data/raw_laws/`
- **Scop:** PDF-uri cu legi, OUG-uri, documente oficiale statice
- **Format:** Fișiere `.pdf`
- **Sursă:** Descărcate manual sau de pe site-uri oficiale
- **Procesare:** `scripts/ingest_laws.py` scanează acest folder

#### `data/scraped_content/`
- **Scop:** Backup text brut extras de pe site-uri prin web scraping
- **Format:** Fișiere `.txt` cu format `anunturi_YYYY_MM_DD.txt`
- **Sursă:** Generat automat de `scripts/scrape_news.py`
- **Utilizare:** 
  - Audit (vezi ce s-a extras)
  - Reproducibilitate (poți reprocesa)
  - Debugging (verifici dacă scraping-ul a funcționat)

#### `data/vector_store/`
- **Scop:** ChromaDB - baza de date vectorială unificată
- **Conținut:** 
  - Embeddings din PDF-uri (legi)
  - Embeddings din web scraping (noutăți)
- **Format:** Fișiere generate automat de ChromaDB
- **Utilizare:** Căutare semantică pentru RAG (folosit de `scripts/find_law.py` și `main.py`)

#### `data/institutions.db`
- **Scop:** SQLite - baza de date cu instituții, adrese, programe
- **Format:** Fișier SQLite
- **Sursă:** Populat de `scripts/setup_sql_db.py`
- **Utilizare:** Interogări Text-to-SQL (folosit de `src/tools/sql.py`)

---

### `/scripts/` - Scripturi ETL

#### `scripts/ingest_laws.py`
- **Input:** PDF-uri din `data/raw_laws/`
- **Proces:**
  1. Load: Extrage text din PDF-uri
  2. Split: Împarte în chunks
  3. Embed: Creează embeddings
  4. Store: Salvează în `data/vector_store/`
- **Output:** Vector store actualizat cu legi

#### `scripts/scrape_news.py`
- **Input:** URL-uri de site-uri oficiale (Primărie, DGASPC, etc.)
- **Proces:**
  1. Scrape: Extrage text de pe site-uri
  2. Backup: Salvează text brut în `data/scraped_content/`
  3. Load: Citește textul
  4. Split: Împarte în chunks (cu metadata `type: "news"`)
  5. Embed: Creează embeddings
  6. Store: Adaugă în **același** `data/vector_store/`
- **Output:** Vector store actualizat cu noutăți

#### `scripts/setup_sql_db.py`
- **Input:** Date dummy sau CSV cu instituții
- **Proces:**
  1. Creează tabelul `institutions` în SQLite
  2. Populează cu date de test
- **Output:** `data/institutions.db` cu date structurate

---

### `/src/` - Codul Aplicației

#### `src/agent.py`
- **Rol:** Orchestratorul principal (creierul agentului)
- **Funcționalitate:**
  - Primește mesajul utilizatorului
  - Decide ce tool să folosească (RAG sau SQL)
  - Execută tool-ul
  - Sintetizează răspunsul

#### `src/prompts.py`
- **Rol:** Definește persona și regulile agentului
- **Conținut:**
  - System prompt
  - Reguli anti-halucinație
  - Formatare răspunsuri

#### `src/tools/sql.py`
- **Rol:** Tool pentru interogare baza de date
- **Funcționalitate:**
  - Primește query natural language
  - Generează SQL query
  - Execută pe `data/institutions.db`
  - Returnează rezultate

#### `src/ui/app.py`
- **Rol:** Interfața Streamlit
- **Funcționalitate:**
  - Chat interface
  - Session state pentru istoric
  - Afișare răspunsuri și surse

---

## 🔄 Fluxul de Date

### 1. Setup Inițial
```
PDF-uri → data/raw_laws/
         ↓
    ingest_laws.py
         ↓
    data/vector_store/ (legi)

Web Scraping → data/scraped_content/
         ↓
    scrape_news.py
         ↓
    data/vector_store/ (noutăți) [ACELAȘI STORE!]
```

### 2. Runtime (Utilizator întreabă)
```
User Query
    ↓
agent.py (decide)
    ↓
    ├─→ RAG Tool → vector_store/ → Răspuns
    └─→ SQL Tool → institutions.db → Răspuns
```

---

## 📝 Note Importante

1. **Vector Store Unificat:** PDF-uri și scraping sunt în același `data/vector_store/` pentru căutare unificată.

2. **Backup Scraping:** Textul brut se salvează în `data/scraped_content/` pentru audit și debugging.

3. **Metadata:** Chunks-urile au metadata diferită (`type: "legislation"` vs `type: "news"`) pentru a distinge sursa.

4. **Separare Date:** SQL-ul este separat de RAG pentru că sunt date structurate (tabele) vs nestructurate (text).

---

## 🚀 Următorii Pași

1. Adaugă PDF-uri în `data/raw_laws/`
2. Rulează `scripts/ingest_laws.py`
3. Configurează `scripts/scrape_news.py` cu URL-uri
4. Rulează `scripts/scrape_news.py`
5. Rulează `scripts/setup_sql_db.py`
6. Pornește aplicația: `streamlit run src/ui/app.py`

