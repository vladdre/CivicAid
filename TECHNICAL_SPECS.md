# 📘 CivicAid – Technical Implementation Specifications

Acest document descrie arhitectura și pașii de implementare pentru **CivicAid**, un agent AI pentru asistență socială și birocratică.

## 🎯 Obiectivul Proiectului

Dezvoltarea unui "Agentic AI" capabil să:

1.  [cite_start]Răspundă la întrebări legislative folosind documente oficiale (**RAG**)[cite: 17].

2.  [cite_start]Localizeze instituții și servicii folosind o bază de date structurată (**Text-to-SQL**)[cite: 18].

3.  [cite_start]Execute pași logici de raționament și acțiune (**Agentic Workflow**)[cite: 12].

-----

## 🔧 TASK 1: Configurare Mediu & Dependințe

**Obiectiv:** Crearea unui mediu de dezvoltare stabil și reproductibil.

### Detalii Tehnice

  * **Virtual Environment:** Este obligatoriu pentru a izola pachetele (evitarea conflictelor de versiuni).

  * **API Management:** Cheile API (OpenAI) nu trebuie niciodată hardcodate. Se va folosi `python-dotenv`.

### Fișiere Critice

1.  **`requirements.txt`**:

      * `langchain`, `langchain-openai`, `langchain-community`: Framework-ul principal pentru orchestrare.

      * `chromadb`: Baza de date vectorială (rulează local, fără costuri de cloud).

      * `pypdf`: Pentru extragerea textului din legile PDF.

      * `requests`, `beautifulsoup4`, `lxml`: Pentru web scraping (extragere noutăți de pe site-uri).

      * `streamlit`: Pentru interfața grafică rapidă.

      * `sqlalchemy`: Pentru conectarea la SQLite.

2.  **`.env`**:

    ```bash

    OPENAI_API_KEY=sk-proj-...

    # LANGCHAIN_TRACING_V2=true (Opțional, pentru debugging în LangSmith)

    ```

-----

## 📚 TASK 2: Data Ingestion Pipeline (RAG)

**Obiectiv:** Implementarea memoriei semantice a agentului ("Creierul Legislativ"). [cite_start]Agentul trebuie să citească PDF-uri și să le indexeze pentru căutare[cite: 20, 21].

### Surse de Date pentru RAG

Sistemul RAG folosește **două tipuri de surse** care sunt procesate și stocate în **același vector store**:

1.  **PDF-uri Statice (Legi):** Documente oficiale, legi, OUG-uri (stabile, rareori se schimbă).

2.  **Web Scraping (Noutăți):** Anunțuri, modificări de proceduri, termene actualizate (dinamice, se schimbă frecvent).

### Structura Directoarelor

```
data/
├── raw_laws/              # PDF-uri cu legi (input pentru ingest_laws.py)
├── scraped_content/       # Text brut extras de pe site-uri (backup pentru audit)
└── vector_store/          # ChromaDB unificat (PDF-uri + Scraping)
```

### Fluxul de Date (ETL) pentru PDF-uri

1.  **Load (Încărcare):**

      * Scriptul `scripts/ingest_laws.py` scanează folderul `data/raw_laws`.

      * Folosește `PyPDFLoader` pentru a încărca fișiere precum *Legea 196/2016 (Venit Minim)* sau *Constituția*.

2.  **Split (Segmentare):**

      * Documentele juridice sunt lungi. Trebuie împărțite în "chunks".

      * **Algoritm:** `RecursiveCharacterTextSplitter`.

      * **Setări:** `chunk_size=1000` (suficient pentru un articol de lege), `chunk_overlap=200` (păstrează contextul între segmente).

3.  **Embed (Vectorizare):**

      * Transformă textul în numere (vectori) folosind `OpenAIEmbeddings`.

4.  **Store (Stocare):**

      * Salvează vectorii în `ChromaDB` (folderul `data/vector_store`). Aceasta permite căutarea semantică (ex: userul caută "bani de căldură", sistemul găsește "ajutor suplimentar pentru energie").

### Fluxul de Date (ETL) pentru Web Scraping

1.  **Scrape (Extragere):**

      * Scriptul `scripts/scrape_news.py` accesează site-uri oficiale (Primărie, DGASPC, etc.).

      * Folosește `requests` + `BeautifulSoup4` pentru a extrage textul relevant.

      * **Backup:** Salvează textul brut în `data/scraped_content/` cu format: `anunturi_YYYY_MM_DD.txt` (pentru audit și reproducibilitate).

2.  **Load (Încărcare):**

      * Citește fișierele text din `data/scraped_content/` sau procesează direct textul extras.

3.  **Split (Segmentare):**

      * Folosește același `RecursiveCharacterTextSplitter` cu aceleași setări.

      * **Metadata critică:** Fiecare chunk primește metadata: `{"type": "news", "date": "2024-01-15", "url": "..."}` pentru a distinge de PDF-uri.

4.  **Embed (Vectorizare):**

      * Folosește același `OpenAIEmbeddings`.

5.  **Store (Stocare):**

      * **Adaugă în ACELAȘI vector store** (`data/vector_store/`) folosind `vector_store.add_documents()`.

      * **Beneficiu:** La căutare RAG, sistemul returnează chunks din ambele surse (PDF-uri + noutăți).

### De ce Același Vector Store?

*   **Căutare Unificată:** Agentul nu trebuie să aleagă manual sursa. RAG-ul caută automat în toate sursele.

*   **Context Complet:** Utilizatorul primește atât legea generală (PDF) cât și noutățile actuale (scraping).

*   **Exemplu:** User întreabă "Când se depun cererile?" → RAG returnează: Legea (PDF) + Termenul actual (scraping).

-----

## 🗄️ TASK 3: Text-to-SQL Database Setup

[cite_start]**Obiectiv:** Implementarea capacității de a interoga date structurate (Locații, Programe)[cite: 18].

### Arhitectura Bazei de Date

Vom folosi **SQLite** (fișier local `institutions.db`) pentru simplitate și portabilitate.

### Schema Tabelului `institutions`

Este critic ca numele coloanelor să fie descriptive, astfel încât LLM-ul să înțeleagă ce reprezintă fără explicații suplimentare.

| Coloană | Tip | Descriere (pentru LLM) | Exemplu |

| :--- | :--- | :--- | :--- |

| `id` | INT | Primary Key | 1 |

| `nume` | TEXT | Numele oficial al instituției | DGASPC Sector 4 |

| `adresa` | TEXT | Adresa fizică completă | Str. Enache Spiridon nr. 12 |

| `tip_serviciu` | TEXT | Cuvinte cheie despre ce face instituția | Asistență Socială, Alocații, Handicap |

| `program` | TEXT | Orele de funcționare | Luni-Joi 08:00-16:00 |

| `grad_ocupare`| TEXT | Info despre aglomerație (Context extra) | Ridicat dimineața |

**Script:** `scripts/setup_sql_db.py` va șterge tabela existentă (dacă e cazul) și o va popula cu date "dummy" relevante pentru demo.

-----

## 🛠️ TASK 4: Tool Definitions ("Mâinile Agentului")

[cite_start]**Obiectiv:** Crearea funcțiilor pe care Agentul le poate "apela" pentru a interacționa cu lumea exterioară[cite: 13].

### 1\. Unealta Legislativă (`src/tools/rag.py`)

  * **Nume:** `consult_legislation`

  * **Descriere (Prompt pentru Agent):** *"Utilizează această unealtă ORI DE CÂTE ORI utilizatorul întreabă despre drepturi, legi, proceduri sau eligibilitate. Nu răspunde din memorie proprie."*

  * **Funcționalitate:**

      * Primește un query text.

      * Caută în ChromaDB cele mai similare 3 pasaje.

      * Formatează output-ul: `Sursă: [Nume Doc] \n Text: [Conținut]`.

### 2\. Unealta de Locații (`src/tools/sql.py`)

  * **Tehnologie:** `SQLDatabaseToolkit` din LangChain.

  * **Funcționalitate:** Permite agentului să transforme întrebarea *"Unde e deschis la sectorul 1?"* în query SQL: `SELECT adresa FROM institutii WHERE sector='1'`.

  * **Bonus:** Această funcționalitate demonstrează capacitatea de "Dynamic SQL Generation".

-----

## 🧠 TASK 5: System Prompt & Persona

**Obiectiv:** Definirea comportamentului, tonului și limitelor agentului ("Guardrails").

### Structura Promptului (`src/prompts.py`)

Agentul **CivicAid** trebuie să respecte următoarele directive:

1.  **Identitate:** Asistent juridic digital ("Mini-Avocat").

2.  **Protocol Anti-Halucinație:**

      * *Regulă:* Dacă informația nu există în contextul RAG, agentul trebuie să spună "Nu am găsit informația în documentele oficiale", nu să inventeze.

3.  **Interacțiune Agentică (Reasoning):**

      * *Regulă:* Nu oferi un verdict de eligibilitate fără date.

      * *Exemplu:* Dacă userul zice "Vreau ajutor", agentul răspunde "Ce venit aveți?" (colectare de parametri).

4.  **Formatare:** Răspunsurile trebuie să fie clare, cu liste (bullet points) și citate (ex: "Conform Art. 5...").

-----

## 🤖 TASK 6: Agent Orchestrator

**Obiectiv:** Asamblarea componentelor într-un sistem cognitiv funcțional.

### Logica de Execuție (`src/agent.py`)

Vom folosi arhitectura **OpenAI Functions Agent**:

1.  **Input:** User Message.

2.  **LLM Processing:** GPT-4o analizează input-ul și prompt-ul de sistem.

3.  **Router (Decizie):**

      * Are nevoie de lege? -\> Cheamă `consult_legislation`.

      * Are nevoie de adresă? -\> Cheamă SQL Tool.

      * Este doar conversație ("Salut")? -\> Răspunde direct.

4.  **Action:** Execută tool-ul selectat.

5.  **Observation:** Primește rezultatul (text din lege sau rânduri din SQL).

6.  **Final Response:** Sintetizează observația într-un răspuns natural pentru utilizator.

-----

## 🖥️ TASK 7: Frontend (Streamlit UI)

[cite_start]**Obiectiv:** Interfața prin care utilizatorul final (Juriul) testează aplicația[cite: 22].

### Componente UI (`src/ui/app.py`)

1.  **Chat Interface:** Stil "WhatsApp" / ChatGPT, familiar utilizatorilor.

2.  **Session State:** Menține istoricul conversației (astfel încât agentul să țină minte contextul de la o replică la alta).

3.  **Feedback Vizual:**

      * Folosirea `st.spinner("Consult legislația...")` pentru a arăta că agentul "gândește".

      * Afișarea surselor (opțional, într-un `st.expander`) pentru a demonstra transparența RAG.

-----

### 🚀 Checklist Final pentru Demo

  * [ ] PDF-urile sunt încărcate și vectorizate (`scripts/ingest_laws.py`).

  * [ ] Web scraping-ul este configurat și rulează (`scripts/scrape_news.py`).

  * [ ] Baza de date SQL are date de test (`scripts/setup_sql_db.py`).

  * [ ] Agentul răspunde corect la "Ce drepturi am?" (RAG - din PDF-uri).

  * [ ] Agentul răspunde corect la "Care sunt ultimele noutăți?" (RAG - din scraping).

  * [ ] Agentul răspunde corect la "Unde găsesc centrul X?" (SQL).

  * [ ] Agentul cere detalii înainte de a confirma eligibilitatea (Reasoning).

---

## 📁 Structura Proiectului

Pentru detalii complete despre structura directoarelor și rolul fiecărui fișier, vezi **`PROJECT_STRUCTURE.md`**.

