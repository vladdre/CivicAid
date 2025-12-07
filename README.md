# CivicAID - Asistent Juridic Inteligent

Sistem cognitiv funcțional pentru consultarea legislației românești și găsirea informațiilor despre instituții publice.

## 🚀 Start Rapid

**Pentru a porni serverul cu toate dependențele configurate automat:**

```bash
python start_server.py
```

Acest script verifică și configurează automat:
- ✅ Vector store (dacă nu există, rulează `ingest_laws.py`)
- ✅ Baza de date SQL (dacă nu există, rulează `setup_sql_db.py`)
- ✅ Server Flask (pornește la `http://localhost:5000`)

Vezi [README_START.md](README_START.md) pentru detalii complete.

## 📁 Structura Proiectului

```
CivicAID/
├── start_server.py          # 🚀 Script principal de start
├── main.py                  # CLI entry point
├── app/
│   ├── agent/              # Agent cognitiv (OpenAI Functions)
│   ├── core/               # Procesare query-uri
│   ├── frontend/            # Aplicația Flask
│   ├── scripts/             # Scripturi utilitare
│   └── tools/               # Unelte (SQL, etc.)
├── data/                    # Date (JSON, DB, vector_store)
└── docs/                    # Documentație
```

## 🛠️ Instalare

1. Clonează repository-ul
2. Instalează dependențele:
   ```bash
   pip install -r requirements.txt
   ```
3. Creează fișierul `.env` cu:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
4. Adaugă PDF-uri cu legi în `data/raw_laws/` (opțional)
5. Rulează:
   ```bash
   python start_server.py
   ```

## 📖 Utilizare

### Server Web
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
python app/agent/agent_main.py
```

## 🔧 Componente

- **Vector Store**: Căutare semantică în legislație folosind ChromaDB
- **SQL Database**: Căutare instituții publice
- **OpenAI Functions Agent**: Decizie automată ce tool să folosească
- **Flask Frontend**: Interfață web pentru utilizatori

## 📚 Documentație

- [README_START.md](README_START.md) - Ghid de start
- [docs/STRUCTURE.md](docs/STRUCTURE.md) - Structura detaliată
- [docs/OPTIMIZATIONS.md](docs/OPTIMIZATIONS.md) - Optimizări
- [app/agent/README.md](app/agent/README.md) - Documentație Agent

## 📝 Licență

Proiect academic pentru consultarea legislației românești.
