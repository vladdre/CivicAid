# 🚀 CivicAid - Ghid de Setup

Acest ghid te ajută să configurezi proiectul CivicAid de la zero.

## 📋 Cerințe Prealabile

- Python 3.10 sau mai nou
- pip (package manager Python)
- Cont OpenAI cu API key (obține de la https://platform.openai.com/api-keys)

---

## 🔑 Pasul 1: Configurare Cheie OpenAI

### Unde pui cheia OpenAI?

**Creează un fișier `.env` în rădăcina proiectului** (același nivel cu `requirements.txt`):

```bash
# În terminal, în directorul proiectului:
cd /home/krpandrei/Projects/VitalLink
touch .env
```

### Conținutul fișierului `.env`:

```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

**⚠️ IMPORTANT:**
- **NU** comite fișierul `.env` în Git (este deja în `.gitignore`)
- **NU** partaja cheia cu nimeni
- Înlocuiește `sk-proj-your-actual-key-here` cu cheia ta reală de la OpenAI

### Cum obții cheia OpenAI?

1. Mergi la https://platform.openai.com/api-keys
2. Loghează-te sau creează cont
3. Click pe "Create new secret key"
4. Copiază cheia (începe cu `sk-proj-` sau `sk-`)
5. O lipești în fișierul `.env`

---

## 📦 Pasul 2: Instalare Dependențe

### Opțiunea 1: Fără Virtual Environment (Nu Recomandat)

```bash
pip install -r requirements.txt
```

### Opțiunea 2: Cu Virtual Environment (Recomandat) ✅

```bash
# Creează virtual environment
python3 -m venv venv

# Activează virtual environment
# Pe Linux/Mac:
source venv/bin/activate
# Pe Windows:
# venv\Scripts\activate

# Instalează dependențele
pip install -r requirements.txt
```

---

## ✅ Pasul 3: Verificare Setup

### Test 1: Verifică că Python poate importa modulele

```bash
python3 -c "import langchain; print('✓ LangChain OK')"
python3 -c "import chromadb; print('✓ ChromaDB OK')"
python3 -c "import openai; print('✓ OpenAI OK')"
```

### Test 2: Verifică că scriptul are sintaxa corectă

```bash
python3 -m py_compile scripts/ingest_laws.py
# Dacă nu apare eroare, totul e OK!
```

### Test 3: Verifică că cheia OpenAI este setată

```bash
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓ API Key:', 'SET' if os.getenv('OPENAI_API_KEY') else '❌ NOT SET')"
```

---

## 📚 Pasul 4: Pregătire Date

### Adaugă PDF-uri cu legi

1. Creează directorul (dacă nu există):
   ```bash
   mkdir -p data/raw_laws
   ```

2. Adaugă fișiere PDF cu legi în `data/raw_laws/`:
   - Exemplu: `legea_196_2016.pdf`, `constitutia.pdf`, etc.

---

## 🧪 Pasul 5: Testare Script Ingestare

### Rulează scriptul de ingestare:

```bash
python3 scripts/ingest_laws.py
```

### Rezultate așteptate:

**Dacă nu ai PDF-uri:**
```
⚠️  No PDF files found in data/raw_laws
📁 Please add PDF files to data/raw_laws and run the script again.
```

**Dacă ai PDF-uri:**
```
🚀 CivicAid - Legal Documents Ingestion Pipeline
============================================================
📚 Found 2 PDF file(s). Loading...
  📄 Loading: legea_196_2016.pdf
    ✓ Loaded 50 pages from legea_196_2016.pdf
  📄 Loading: constitutia.pdf
    ✓ Loaded 20 pages from constitutia.pdf

✂️  Splitting documents into chunks (size=1000, overlap=200)...
  ✓ Created 150 chunks from 70 documents

🔢 Creating embeddings using OpenAI...
💾 Storing vectors in ChromaDB at data/vector_store...
  ✓ Vector store created/updated successfully!
  ✓ Total documents indexed: 150

============================================================
✅ Ingestion pipeline completed successfully!
============================================================

📊 Summary:
   • PDF files processed: 2
   • Total pages: 70
   • Total chunks: 150
   • Vector store location: data/vector_store

💡 You can now use the vector store in your RAG tool!
```

---

## ❌ Rezolvare Probleme

### Eroare: "OPENAI_API_KEY not found"

**Soluție:**
1. Verifică că ai creat fișierul `.env` în rădăcina proiectului
2. Verifică că conține exact: `OPENAI_API_KEY=sk-proj-...`
3. Verifică că nu ai spații în jurul `=`
4. Rulează din nou scriptul

### Eroare: "No module named 'langchain'"

**Soluție:**
```bash
pip install -r requirements.txt
```

### Eroare: "No PDF files found"

**Soluție:**
- Adaugă fișiere PDF în `data/raw_laws/`
- Verifică că fișierele au extensia `.pdf`

---

## ✅ Checklist Final

- [ ] Fișier `.env` creat cu `OPENAI_API_KEY`
- [ ] Dependențele instalate (`pip install -r requirements.txt`)
- [ ] PDF-uri adăugate în `data/raw_laws/`
- [ ] Scriptul `ingest_laws.py` rulează fără erori
- [ ] Vector store creat în `data/vector_store/`

---

## 🎯 Următorii Pași

După ce Task 1 și 2 sunt complete:
- Task 3: Setup SQL Database (`scripts/setup_sql_db.py`)
- Task 4: Tool Definitions (`src/tools/sql.py`, `scripts/find_law.py`)
- Task 5: System Prompt (`src/prompts.py`)
- Task 6: Agent Orchestrator (`src/agent.py`)
- Task 7: Frontend (`src/ui/app.py`)

