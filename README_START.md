# 🚀 Pornire CivicAID Server

## Start Rapid

Pentru a porni serverul cu toate dependențele configurate automat:

```bash
python start_server.py
```

## Ce face scriptul?

Scriptul `start_server.py` verifică și configurează automat:

1. **Vector Store** - Dacă nu există, rulează `ingest_laws.py` pentru a crea vector store-ul din PDF-uri
2. **Baza de Date SQL** - Dacă nu există, rulează `setup_sql_db.py` pentru a crea baza de date cu instituții
3. **Server Flask** - Pornește serverul la `http://localhost:5000`

## Cerințe Prealabile

1. **Variabile de mediu**: Creează fișierul `.env` cu:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

2. **PDF-uri legi** (opțional): Adaugă PDF-uri cu legi în `data/raw_laws/` pentru a crea vector store

3. **Instituții JSON** (opțional): Asigură-te că există `data/institutions.json` pentru baza de date SQL

## Structura Fișierelor

```
CivicAID/
├── start_server.py          # 🚀 Script principal de start
├── main.py                  # CLI entry point
├── app/
│   ├── agent/
│   │   └── agent_main.py   # Agent CLI
│   ├── core/
│   ├── frontend/
│   ├── scripts/
│   └── tools/
├── data/
│   ├── raw_laws/           # PDF-uri legi (adaugă manual)
│   ├── vector_store/       # Creat automat
│   ├── institutions.json   # Date instituții
│   └── institutions.db     # Creat automat
└── docs/
```

## Alte Comenzi

### CLI pentru query-uri:
```bash
python main.py "Mesajul tău"
```

### Agent CLI:
```bash
python app/agent/agent_main.py
```

### Setup manual (dacă e nevoie):
```bash
# Vector store
python -m app.scripts.ingest_laws

# Baza de date SQL
python -m app.scripts.setup_sql_db
```

## Note

- Scriptul verifică automat ce lipsește și îl creează
- Dacă lipsesc PDF-uri sau `institutions.json`, scriptul va continua dar unele funcții nu vor funcționa
- Serverul pornește în mod `debug=True` pentru dezvoltare

