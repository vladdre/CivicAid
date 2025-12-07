# Structura Proiectului CivicAID

## Organizare Foldere

```
CivicAID/
├── app/                          # Codul principal al aplicației
│   ├── __init__.py
│   ├── core/                     # Funcționalități principale
│   │   ├── __init__.py
│   │   └── query_processor.py    # Procesarea query-urilor (fost main.py)
│   ├── frontend/                 # Aplicația Flask
│   │   ├── __init__.py
│   │   ├── app.py                # Aplicația Flask principală
│   │   ├── query_classifier.py  # Clasificarea query-urilor
│   │   ├── title_generator.py    # Generarea titlurilor conversațiilor
│   │   ├── static/                # Fișiere statice (CSS, JS, imagini)
│   │   └── templates/             # Template-uri HTML
│   ├── scripts/                  # Scripturi utilitare
│   │   ├── __init__.py
│   │   ├── find_law.py           # Căutare în vector store
│   │   ├── ingest_laws.py        # Ingestie PDF-uri
│   │   └── setup_sql_db.py       # Setup baza de date SQL
│   └── tools/                     # Unelte
│       ├── __init__.py
│       └── sql.py                # Tool pentru interogări SQL
├── data/                         # Date
│   ├── vector_store/             # Vector store ChromaDB
│   ├── raw_laws/                 # PDF-uri cu legi (de adăugat manual)
│   ├── chat.json                 # Baza de date conversații
│   ├── users.json                # Baza de date utilizatori
│   ├── institutions.json          # Date instituții
│   └── institutions.db            # Baza de date SQLite
├── docs/                         # Documentație
│   ├── OPTIMIZATIONS.md
│   ├── PROJECT_STRUCTURE.md
│   ├── SETUP.md
│   ├── TECHNICAL_SPECS.md
│   └── TASK_VERIFICATION.md
├── tests/                        # Teste
│   ├── test_db.py
│   ├── test_sql_tool.py
│   └── ...
├── main.py                       # Entry point CLI
├── requirements.txt               # Dependențe Python
├── README.md                      # Documentație principală
└── .env                          # Variabile de mediu (nu se versionizează)
```

## Importuri

### Din root sau alte module:
```python
# Pentru query processor
from app.core.query_processor import process_query

# Pentru frontend
from app.frontend.app import app
from app.frontend.title_generator import generate_conversation_title
from app.frontend.query_classifier import needs_database_results

# Pentru scripts
from app.scripts.find_law import find_relevant_laws
from app.scripts.ingest_laws import load_pdfs, create_vector_store

# Pentru tools
from app.tools.sql import query_institutions
```

## Căi Importante

- **Vector Store**: `data/vector_store/`
- **PDF-uri legi**: `data/raw_laws/`
- **Baza de date chat**: `data/chat.json`
- **Baza de date utilizatori**: `data/users.json`
- **Baza de date SQL**: `data/institutions.db`

## Rulare

### CLI:
```bash
python main.py "Mesajul tău"
```

### Flask App:
```bash
cd app/frontend
python app.py
```

Sau:
```bash
python -m app.frontend.app
```

