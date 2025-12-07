# 📚 CivicAID - Documentație Completă Consolidată

> **Asistent Juridic Inteligent** - Sistem cognitiv funcțional pentru consultarea legislației românești și găsirea informațiilor despre instituții publice.

---

## 📋 Cuprins

1. [Prezentare Generală](#prezentare-generală)
2. [Structura Completă a Proiectului](#structura-completă-a-proiectului)
3. [Detalii Fișiere](#detalii-fișiere)
4. [Instalare și Configurare](#instalare-și-configurare)
5. [Utilizare](#utilizare)
6. [Arhitectură Tehnică](#arhitectură-tehnică)
7. [Componente Principale](#componente-principale)
8. [Optimizări](#optimizări)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Prezentare Generală

CivicAID este un sistem AI care ajută cetățenii români să:
- **Consulte legislația** folosind RAG (Retrieval-Augmented Generation)
- **Găsească instituții publice** folosind Text-to-SQL
- **Genereze cereri oficiale** (ex: ANPC) automat
- **Interacționeze natural** prin chat web sau CLI

### Tehnologii Folosite

- **LangChain** - Framework pentru orchestrarea AI
- **ChromaDB** - Baza de date vectorială pentru RAG
- **OpenAI GPT-4o** - Model de limbaj pentru generare și embeddings
- **Flask** - Framework web pentru interfața utilizator
- **SQLite** - Baza de date pentru instituții
- **SQLAlchemy** - ORM pentru interogări SQL

---

## 📁 Structura Completă a Proiectului

```
CivicAID/
├── 📄 README.md                      # Documentația principală
├── 📄 README_START.md                # Ghid de start rapid
├── 📄 COMPLETE_DOCUMENTATION.md      # Acest fișier (documentație consolidată)
├── 📄 requirements.txt               # Dependențe Python
├── 📄 .env                           # Variabile de mediu (nu se versionizează)
├── 📄 .gitignore                     # Fișiere ignorate de Git
│
├── 🚀 start_server.py                # Script principal de start automat
├── 📝 main.py                        # Entry point CLI
├── 🕷️ scrapper.py                    # Scraper Monitor Oficial
├── 🔍 check_progress.py              # Verificare progres scraper
├── ✅ verify_extraction.py            # Verificare extragere date
├── 🧪 test_scraper.py                # Teste pentru scraper
├── 📊 checkpoint.json                 # Checkpoint pentru scraper
├── 📋 legi.json                      # Legi extrase din Monitor Oficial
│
├── 📂 app/                           # Codul principal al aplicației
│   ├── __init__.py
│   │
│   ├── 🤖 agent/                     # Agent cognitiv (OpenAI Functions)
│   │   ├── __init__.py
│   │   ├── agent.py                  # Logica principală a agentului
│   │   ├── agent_main.py             # Entry point CLI pentru agent
│   │   ├── tools.py                  # Definiții tool-uri pentru OpenAI Functions
│   │   └── README.md                 # Documentație agent
│   │
│   ├── 🧠 core/                       # Funcționalități principale
│   │   ├── __init__.py
│   │   └── query_processor.py       # Procesarea query-urilor (RAG + SQL)
│   │
│   ├── 🖥️ frontend/                   # Aplicația Flask
│   │   ├── __init__.py
│   │   ├── app.py                    # Aplicația Flask principală
│   │   ├── query_classifier.py       # Clasificarea query-urilor
│   │   ├── title_generator.py        # Generarea titlurilor conversațiilor
│   │   ├── static/                   # Fișiere statice (CSS, JS, imagini)
│   │   │   ├── css/
│   │   │   ├── js/
│   │   │   └── images/
│   │   └── templates/                # Template-uri HTML
│   │       ├── index.html
│   │       ├── login.html
│   │       └── register.html
│   │
│   ├── 🔧 scripts/                    # Scripturi utilitare
│   │   ├── __init__.py
│   │   ├── find_law.py                # Căutare în vector store
│   │   ├── ingest_laws.py            # Ingestie PDF-uri în vector store
│   │   ├── ingest_json_laws.py      # Ingestie legi.json în vector store
│   │   ├── setup_sql_db.py       # Setup baza de date SQL
│   │   ├── README_FIND_LAW.md        # Documentație find_law.py
│   │   └── EXPLAIN_EMBEDDINGS.md     # Explicație embeddings
│   │
│   └── 🛠️ tools/                      # Unelte
│       ├── __init__.py
│       ├── sql.py                     # Tool pentru interogări SQL (Text-to-SQL)
│       └── anpc_form.py               # Tool pentru generare cereri ANPC
│
├── 📂 data/                          # Date
│   ├── vector_store/                 # Vector store ChromaDB (PDF-uri)
│   ├── vector_store_json/            # Vector store ChromaDB (legi.json)
│   ├── raw_laws/                     # PDF-uri cu legi (de adăugat manual)
│   ├── scraped_content/              # Text brut extras de pe site-uri
│   ├── generated_forms/              # Formulare generate
│   ├── chat.json                     # Baza de date conversații
│   ├── users.json                    # Baza de date utilizatori
│   ├── institutions.json              # Date instituții
│   ├── institutions.db                # Baza de date SQLite
│   ├── output.txt                    # Output temporar
│   ├── search_results.txt            # Rezultate căutare
│   └── cerere_ANPC.txt               # Template cereri
│
├── 📂 docs/                          # Documentație
│   ├── PROJECT_STRUCTURE.md           # Structura detaliată a proiectului
│   ├── TASK_VERIFICATION.md          # Verificare task-uri
│   ├── STRUCTURE.md                  # Structura proiectului
│   ├── SETUP.md                      # Ghid de setup
│   ├── OPTIMIZATIONS.md              # Optimizări implementate
│   └── TECHNICAL_SPECS.md            # Specificații tehnice detaliate
│
├── 📂 tests/                         # Teste
│   ├── test_db.py                    # Teste baza de date
│   ├── test_sql_tool.py              # Teste tool SQL
│   ├── test_vector_store.py          # Teste vector store
│   ├── analyze_quality.py            # Analiză calitate
│   └── debug_embeddings.py           # Debug embeddings
│
└── 📂 frontend/                      # Frontend alternativ (legacy)
    └── frontend/
        └── app.py
```

---

## 📄 Detalii Fișiere

### 🚀 Fișiere Root

#### `start_server.py`
**Scop:** Script principal de start automat care verifică și configurează toate dependențele.

**Funcționalități:**
- Verifică existența vector store-ului (PDF și JSON)
- Creează vector store-ul dacă nu există (rulează `ingest_laws.py` și `ingest_json_laws.py`)
- Verifică existența bazei de date SQL
- Creează baza de date SQL dacă nu există (rulează `setup_sql_db.py`)
- Pornește serverul Flask la `http://localhost:5000`

**Utilizare:**
```bash
python start_server.py
```

#### `main.py`
**Scop:** Entry point pentru CLI (Command Line Interface).

**Funcționalități:**
- Primește mesajul utilizatorului ca argument
- Procesează query-ul folosind `process_query()`
- Afișează rezultatul în consolă

**Utilizare:**
```bash
python main.py "Am fost implicat intr un accident auto. Celalalt sofer a plecta. Ce pot face?"
```

#### `scrapper.py`
**Scop:** Scraper pentru Monitor Oficial - tracking modificări legi.

**Funcționalități:**
- Descarcă documente PDF de pe Monitor Oficial
- Extrage text din PDF-uri folosind PyPDF2
- Identifică legi menționate în documente
- Trackează ultima mențiune și ultima modificare pentru fiecare lege
- Salvează rezultatele în `legi.json`

**Utilizare:**
```bash
python scrapper.py
```

#### `check_progress.py`
**Scop:** Verificare progres scraper.

#### `verify_extraction.py`
**Scop:** Verificare extragere date din scraper.

#### `test_scraper.py`
**Scop:** Teste pentru scraper.

---

### 🤖 Agent (`app/agent/`)

#### `agent.py`
**Scop:** Agent cognitiv funcțional folosind OpenAI Functions Agent.

**Clase:**
- `Agent`: Clasa principală a agentului

**Metode principale:**
- `__init__(model, temperature)`: Inițializează agentul
- `chat(user_message)`: Metodă simplificată pentru chat
- `process(user_message, max_iterations)`: Procesează mesajul folosind arhitectura OpenAI Functions
- `_execute_tool(tool_name, arguments)`: Execută un tool specificat
- `add_to_history(role, content)`: Adaugă mesaj în istoric
- `clear_history()`: Șterge istoricul conversației

**Arhitectură:**
1. Input: User Message
2. LLM Processing: GPT-4o analizează input-ul
3. Router (Decizie): Decide ce tool să folosească
4. Action: Execută tool-ul selectat
5. Observation: Primește rezultatul
6. Final Response: Sintetizează răspunsul

#### `agent_main.py`
**Scop:** Entry point CLI pentru agent.

**Moduri:**
- **Interactiv:** `python app/agent/agent_main.py`
- **CLI cu mesaj:** `python app/agent/agent_main.py "Mesajul tău"`

#### `tools.py`
**Scop:** Definiții tool-uri pentru OpenAI Functions.

**Tool-uri disponibile:**
1. `consult_legislation`: Consultă legislația română
2. `get_institution_address`: Găsește adrese instituții publice

**Funcții:**
- `consult_legislation(user_message, conversation_history)`: Consultă legislația
- `get_institution_address(user_message, conversation_history)`: Găsește instituții

**Definiții:**
- `TOOLS_DEFINITIONS`: Listă de definiții tool-uri pentru OpenAI
- `TOOLS_MAP`: Mapare funcții pentru execuție

---

### 🧠 Core (`app/core/`)

#### `query_processor.py`
**Scop:** Procesarea principală a query-urilor (RAG + SQL + forms).

**Funcții principale:**
- `process_query(user_message, conversation_history, verbose, refresh_token, username)`: Funcția principală de procesare
- `check_vector_store_exists()`: Verifică existența vector store-ului (cu cache)
- `create_vector_store()`: Creează vector store-ul rulând `ingest_laws.py`
- `run_find_law(user_message, conversation_history, verbose)`: Rulează căutarea în vector store
- `summarize_results(results, user_query, conversation_history, verbose)`: Sintetizează rezultatele
- `is_summary_relevant(summary, user_query, api_key)`: Verifică relevanța rezumatului
- `search_in_json_files(user_query, api_key, verbose)`: Caută în vector store-ul JSON
- `write_output_to_file(output, output_file)`: Scrie output în fișier (doar pentru CLI)

**Flux de procesare:**
1. Verifică dacă este cerere de formular ANPC
2. Verifică/creează vector store
3. Rulează `find_law.py` pentru căutare semantică
4. Generează rezumat sintetizat
5. Verifică relevanța rezumatului
6. Caută în vector store JSON ca fallback
7. Returnează rezultatul final

---

### 🖥️ Frontend (`app/frontend/`)

#### `app.py`
**Scop:** Aplicația Flask principală pentru interfața web.

**Rute:**
- `GET /`: Pagina principală (chat interface)
- `GET /login`: Pagina de login
- `POST /login`: Procesare login
- `GET /register`: Pagina de înregistrare
- `POST /register`: Procesare înregistrare
- `GET /logout`: Logout
- `GET /api/conversations`: Obține lista conversațiilor
- `GET /api/conversations/<id>`: Obține mesajele unei conversații
- `POST /api/chat`: Procesează mesajul utilizatorului
- `POST /api/voice-to-text`: Conversie audio în text
- `DELETE /api/conversations/<id>`: Șterge conversația
- `GET /auth/google`: Inițiază OAuth flow pentru Gmail
- `GET /auth/google/callback`: Procesează callback OAuth
- `GET /api/user/refresh-token`: Obține refresh token utilizator

**Funcționalități:**
- Autentificare utilizatori (login/register)
- Chat interface cu istoric conversații
- Voice-to-text pentru input vocal
- OAuth Google pentru trimitere email ANPC
- Gestionare sesiuni și conversații

#### `query_classifier.py`
**Scop:** Clasificarea query-urilor pentru a determina dacă necesită rezultate din baza de date.

**Funcții:**
- `needs_database_results(message, conversation_history)`: Determină dacă query-ul necesită rezultate SQL

#### `title_generator.py`
**Scop:** Generarea titlurilor pentru conversații.

**Funcții:**
- `generate_conversation_title(message)`: Generează titlu pentru conversație folosind OpenAI

#### Templates HTML
- `index.html`: Interfața principală de chat
- `login.html`: Pagina de login
- `register.html`: Pagina de înregistrare

---

### 🔧 Scripts (`app/scripts/`)

#### `ingest_laws.py`
**Scop:** Data Ingestion Pipeline pentru PDF-uri - creează vector store din PDF-uri.

**Funcții:**
- `load_pdfs(raw_laws_dir)`: Încarcă PDF-uri din `data/raw_laws/`
- `split_documents(documents, chunk_size, chunk_overlap)`: Împarte documentele în chunks
- `create_vector_store(chunks, vector_store_dir)`: Creează embeddings și le salvează în ChromaDB
- `main()`: Execuție principală a pipeline-ului

**Parametri:**
- `CHUNK_SIZE = 1000`: Dimensiunea chunk-urilor
- `CHUNK_OVERLAP = 200`: Suprapunerea între chunks

**Utilizare:**
```bash
python -m app.scripts.ingest_laws
```

#### `ingest_json_laws.py`
**Scop:** Data Ingestion Pipeline pentru `legi.json` - creează vector store din JSON.

**Funcții:**
- `load_json_laws(legi_json_path)`: Încarcă legile din `legi.json`
- `split_documents(documents, chunk_size, chunk_overlap)`: Împarte documentele în chunks
- `create_vector_store(chunks, vector_store_dir)`: Creează embeddings și le salvează în ChromaDB
- `main()`: Execuție principală

**Utilizare:**
```bash
python -m app.scripts.ingest_json_laws
```

#### `find_law.py`
**Scop:** Găsirea articolelor de lege relevante pe baza unui mesaj.

**Funcții:**
- `extract_keywords_and_query(user_message, api_key, conversation_history, verbose)`: Optimizează query-ul folosind LLM
- `find_relevant_laws(user_message, k, use_optimization, conversation_history, verbose)`: Găsește articole relevante
- `format_results(results)`: Formatează rezultatele pentru afișare
- `main()`: Funcția principală (CLI)

**Parametri:**
- `k = 5`: Numărul de rezultate returnate
- `use_optimization = True`: Dacă să optimizeze query-ul

**Utilizare:**
```bash
python -m app.scripts.find_law "Am avut un accident de mașină"
```

#### `setup_sql_db.py`
**Scop:** Crearea și popularea bazei de date SQLite cu instituții.

**Funcții:**
- `load_institutions_from_json(json_file)`: Încarcă datele din `data/institutions.json`
- `create_database(db_file)`: Creează baza de date SQLite
- `populate_database(session, institutions)`: Populează baza de date
- `verify_database(session)`: Verifică conținutul bazei de date
- `main()`: Execuție principală

**Schema tabelului `institutions`:**
- `id`: Primary Key
- `nume`: Numele instituției
- `adresa`: Adresa completă
- `tip_serviciu`: Cuvinte cheie despre servicii
- `program`: Orele de funcționare
- `grad_ocupare`: Info despre aglomerație

**Utilizare:**
```bash
python -m app.scripts.setup_sql_db
```

---

### 🛠️ Tools (`app/tools/`)

#### `sql.py`
**Scop:** Tool pentru interogare baza de date SQL folosind Text-to-SQL.

**Funcții:**
- `get_api_key()`: Obține cheia API OpenAI din `.temp`, `.tmp` sau `.env`
- `get_sql_database()`: Creează și returnează obiect SQLDatabase
- `query_institutions(natural_language_query, vector_store_output, conversation_history)`: Transformă query natural în SQL și execută
- `format_sql_results(result)`: Formatează rezultatele SQL
- `save_results_to_file(query, results, vector_store_output, sql_query)`: Salvează rezultatele în fișier

**Utilizare:**
```python
from app.tools.sql import query_institutions
result = query_institutions("Unde găsesc case de pensii?")
```

#### `anpc_form.py`
**Scop:** Tool pentru generarea automată a cererilor oficiale (ex: ANPC).

**Funcții:**
- `detect_form_request(message, conversation_history)`: Detectează dacă mesajul cere generarea unui formular
- `request_user_info()`: Returnează mesajul pentru cererea informațiilor necesare
- `extract_user_info_from_conversation(conversation_history, current_message)`: Extrage informațiile utilizatorului
- `complete_form_template(user_info, conversation_context)`: Completează template-ul cererii
- `send_email_with_gmail_api(form_text, sender_email, recipient_email, refresh_token, user_name)`: Trimite email prin Gmail API
- `send_email_with_form(form_text, sender_email, recipient_email, user_name, refresh_token)`: Trimite email (Gmail API sau SMTP)
- `generate_pdf_from_text(text, output_filename)`: Generează PDF din text
- `is_continuing_form_conversation(conversation_history)`: Verifică dacă conversația continuă un proces de formular
- `get_user_email_from_db(username)`: Obține email-ul utilizatorului din baza de date
- `generate_anpc_form(user_message, conversation_history, refresh_token, username, verbose)`: Funcția principală

**Utilizare:**
```python
from app.tools.anpc_form import generate_anpc_form
result = generate_anpc_form("Vreau să generez o cerere ANPC", conversation_history)
```

---

## 🔧 Instalare și Configurare

### Cerințe Prealabile

- Python 3.10 sau mai nou
- pip (package manager Python)
- Cont OpenAI cu API key

### Pasul 1: Clonează Repository-ul

```bash
git clone <repository-url>
cd CivicAID
```

### Pasul 2: Creează Virtual Environment (Recomandat)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### Pasul 3: Instalează Dependențe

```bash
pip install -r requirements.txt
```

**Dependențe principale:**
- `langchain`, `langchain-openai`, `langchain-community`, `langchain-text-splitters`, `langchain-core`
- `chromadb` - Baza de date vectorială
- `pypdf`, `PyPDF2` - Procesare PDF
- `openai` - OpenAI SDK
- `flask` - Framework web
- `sqlalchemy` - ORM pentru SQL
- `python-dotenv` - Variabile de mediu
- `reportlab` - Generare PDF
- `google-auth`, `google-auth-oauthlib`, `google-api-python-client` - Google OAuth
- `SpeechRecognition`, `pyaudio`, `pydub` - Recunoaștere vocală
- `requests`, `beautifulsoup4`, `lxml` - Web scraping

### Pasul 4: Configurare Variabile de Mediu

Creează fișierul `.env` în rădăcina proiectului:

```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Pasul 5: Pregătire Date

1. **Adaugă PDF-uri cu legi:**
   ```bash
   mkdir -p data/raw_laws
   # Adaugă PDF-uri în data/raw_laws/
   ```

2. **Adaugă date instituții:**
   ```bash
   # Creează data/institutions.json cu datele instituțiilor
   ```

### Pasul 6: Start Server

```bash
python start_server.py
```

Scriptul va:
- Verifica și crea vector store-ul dacă nu există
- Verifica și crea baza de date SQL dacă nu există
- Porni serverul Flask la `http://localhost:5000`

---

## 🚀 Utilizare

### Server Web (Recomandat)

```bash
python start_server.py
```

Apoi deschide `http://localhost:5000` în browser.

### CLI pentru Query-uri

```bash
python main.py "Ce drepturi am ca pensionar?"
```

### Agent CLI

```bash
# Mod interactiv
python app/agent/agent_main.py

# Mod CLI cu mesaj
python app/agent/agent_main.py "Ce drepturi am ca pensionar?"
```

### Scripturi Manuale

```bash
# Creare vector store din PDF-uri
python -m app.scripts.ingest_laws

# Creare vector store din legi.json
python -m app.scripts.ingest_json_laws

# Setup baza de date SQL
python -m app.scripts.setup_sql_db

# Căutare în vector store
python -m app.scripts.find_law "Am avut un accident de mașină"
```

---

## 🏗️ Arhitectură Tehnică

### Fluxul de Date (ETL)

#### 1. Setup Inițial

```
PDF-uri → data/raw_laws/
         ↓
    ingest_laws.py
         ↓
    data/vector_store/ (legi)

legi.json
         ↓
    ingest_json_laws.py
         ↓
    data/vector_store_json/ (legi JSON)

institutions.json
         ↓
    setup_sql_db.py
         ↓
    data/institutions.db
```

#### 2. Runtime (Utilizator întreabă)

```
User Query
    ↓
query_processor.py
    ↓
    ├─→ Verifică formular ANPC?
    │       ↓
    │   anpc_form.py → Generează și trimite cerere
    │
    ├─→ Necesită legislație?
    │       ↓
    │   find_law.py → Vector Store → Rezumat
    │
    └─→ Necesită instituții?
            ↓
        sql.py → Text-to-SQL → institutions.db → Rezultate
```

### Arhitectura Agentului

```
User Message
    ↓
Agent (agent.py)
    ↓
OpenAI Functions API
    ↓
Router Decision
    ├─→ consult_legislation → query_processor → Vector Store
    ├─→ get_institution_address → sql.py → SQL Database
    └─→ Direct Response (conversație simplă)
    ↓
Synthesize Response
    ↓
User Response
```

---

## 🧩 Componente Principale

### 1. Vector Store (RAG)

**Tehnologie:** ChromaDB cu OpenAI Embeddings

**Proces:**
1. **Load:** PDF-uri → Text (PyPDFLoader)
2. **Split:** Text → Chunks (RecursiveCharacterTextSplitter, size=1000, overlap=200)
3. **Embed:** Chunks → Vectors (OpenAIEmbeddings, text-embedding-3-small)
4. **Store:** Vectors → ChromaDB

**Căutare:**
- Query → Embedding → Similarity Search → Top K chunks → Rezumat

### 2. SQL Database (Text-to-SQL)

**Tehnologie:** SQLite + SQLAlchemy + LangChain SQLDatabase

**Proces:**
1. Query natural language
2. LLM generează SQL query
3. Execută pe SQLite
4. Formatează rezultatele

### 3. ANPC Form Generator

**Tehnologie:** OpenAI GPT-4o + Gmail API / SMTP

**Proces:**
1. Detectează cererea de formular
2. Extrage informații utilizator
3. Completează template folosind AI
4. Generează PDF (opțional)
5. Trimite email prin Gmail API sau SMTP

### 4. Frontend Web

**Tehnologie:** Flask + HTML/CSS/JavaScript

**Funcționalități:**
- Autentificare utilizatori
- Chat interface cu istoric
- Voice-to-text
- OAuth Google pentru email
- Gestionare conversații

---

## ⚡ Optimizări

### Implementate ✅

1. **Scrierea în fișier eliminată pentru API calls** - Reducere latență
2. **Print statements optimizate** - Parametru `verbose` (default: False)
3. **Generarea titlului asincronă** - Nu mai blochează răspunsul
4. **Cache pentru vector store** - Evită verificări redundante
5. **Lazy loading vector store** - Reutilizează instanța

### Posibile (Viitor)

1. Apeluri OpenAI paralele (asyncio)
2. Optimizarea prompt-urilor
3. Caching pentru rezultate similare
4. Database connection pooling

---

## 🔍 Troubleshooting

### Eroare: "OPENAI_API_KEY not found"

**Soluție:**
1. Verifică că ai creat fișierul `.env` în rădăcina proiectului
2. Verifică că conține exact: `OPENAI_API_KEY=sk-proj-...`
3. Verifică că nu ai spații în jurul `=`

### Eroare: "Vector store nu există"

**Soluție:**
```bash
python -m app.scripts.ingest_laws
```

### Eroare: "No module named 'langchain'"

**Soluție:**
```bash
pip install -r requirements.txt
```

### Nu găsește rezultate relevante

**Cauze posibile:**
- PDF-urile nu conțin informații relevante
- Vector store-ul nu a fost actualizat
- Mesajul este prea specific sau prea general

**Soluție:**
- Verifică ce PDF-uri ai în `data/raw_laws/`
- Rulează din nou `ingest_laws.py` pentru a reindexa
- Încearcă să reformulezi mesajul

### Eroare: "Baza de date SQL nu există"

**Soluție:**
```bash
python -m app.scripts.setup_sql_db
```

### Server Flask nu pornește

**Soluție:**
- Verifică că portul 5000 nu este deja folosit
- Verifică că toate dependențele sunt instalate
- Verifică log-urile pentru erori

---

## 📊 Statistici Proiect

- **Total fișiere Python:** 33
- **Total fișiere Markdown:** 11
- **Liniile de cod:** ~10,000+
- **Componente principale:** 4 (RAG, SQL, ANPC Forms, Frontend)
- **Tool-uri disponibile:** 2 (consult_legislation, get_institution_address)

---

## 📝 Licență

Proiect academic pentru consultarea legislației românești.

---

## 🔗 Referințe

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**Ultima actualizare:** Consolidare documentație - Toate fișierele .md comprimate într-un singur document complet.

