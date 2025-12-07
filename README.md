# CivicAID - Intelligent Legal Assistant

> **Functional cognitive system** for consulting Romanian legislation and finding information about public institutions.

CivicAID is an AI system that helps Romanian citizens to:
- **Consult legislation** using RAG (Retrieval-Augmented Generation)
- **Find public institutions** using Text-to-SQL
- **Generate official requests** (e.g.: ANPC) automatically
- **Interact naturally** through web chat or CLI

---

## 🚀 Quick Start

**To start the server with all dependencies configured automatically:**

```bash
python start_server.py
```

This script automatically checks and configures:
- ✅ Vector store (if it doesn't exist, runs `ingest_laws.py`)
- ✅ SQL database (if it doesn't exist, runs `setup_sql_db.py`)
- ✅ Flask server (starts at `http://localhost:5000`)

See [README_START.md](README_START.md) for complete details.

---

## 📁 Project Structure

```
CivicAID/
├── start_server.py          # 🚀 Main automatic start script
├── main.py                  # CLI entry point
├── app/
│   ├── agent/              # Cognitive agent (OpenAI Functions)
│   ├── core/               # Query processing
│   ├── frontend/            # Flask application
│   ├── scripts/             # Utility scripts
│   └── tools/               # Tools (SQL, forms, etc.)
├── data/                    # Data (JSON, DB, vector_store)
└── docs/                    # Documentation
```

---

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd CivicAID
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file:**
   ```bash
   OPENAI_API_KEY=your-api-key-here
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

4. **Add PDF files with laws** (optional):
   ```bash
   mkdir -p data/raw_laws
   # Add PDFs to data/raw_laws/
   ```

5. **Start the server:**
   ```bash
   python start_server.py
   ```

---

## 📖 Usage

### Web Server (Recommended)

```bash
python start_server.py
```

Then open `http://localhost:5000` in your browser.

### CLI for Queries

```bash
python main.py "Am fost implicat intr un accident auto. Celalalt sofer a plecta. Ce pot face?"
```

### Agent CLI

```bash
# Interactive mode
python app/agent/agent_main.py

# CLI with message
python app/agent/agent_main.py "Your message"
```

---

## 🔧 Main Components

- **Vector Store (RAG)**: Semantic search in legislation using ChromaDB
  - Loads PDFs/JSON → Splits into chunks → Creates embeddings → Stores in ChromaDB
  - Search: Query → Embedding → Similarity Search → Summary

- **SQL Database (Text-to-SQL)**: Search public institutions
  - Natural language query → LLM generates SQL → Executes on SQLite → Formats results

- **OpenAI Functions Agent**: Automatic decision on which tool to use
  - Routes queries to appropriate tool (legislation, institutions, or direct response)

- **Form Generator**: Automatic generation of official requests
  - Detects form requests → Extracts user info → Completes template → Sends email

- **Flask Frontend**: Web interface for users
  - User authentication, chat interface, voice-to-text, Google OAuth

---

## 🏗️ Technologies Used

- **LangChain** - Framework for orchestrating AI
- **ChromaDB** - Vector database for RAG
- **OpenAI GPT-4o** - Language model for generation and embeddings
- **Flask** - Web framework for user interface
- **SQLite** - Database for institutions
- **SQLAlchemy** - ORM for SQL queries

---

## 📚 Documentation

For complete documentation, see:

- **[COMPLETE_DOCUMENTATION.md](COMPLETE_DOCUMENTATION.md)** - Complete consolidated documentation with all details
- [README_START.md](README_START.md) - Quick start guide
- [docs/STRUCTURE.md](docs/STRUCTURE.md) - Detailed structure
- [docs/OPTIMIZATIONS.md](docs/OPTIMIZATIONS.md) - Optimizations
- [app/agent/README.md](app/agent/README.md) - Agent documentation

---

## 🔍 Quick Troubleshooting

### Error: "OPENAI_API_KEY not found"
- Check that you created `.env` file in project root
- Verify it contains: `OPENAI_API_KEY=sk-proj-...`

### Error: "Vector store does not exist"
```bash
python -m app.scripts.ingest_laws
```

### Error: "No module named 'langchain'"
```bash
pip install -r requirements.txt
```

For more troubleshooting, see [COMPLETE_DOCUMENTATION.md](COMPLETE_DOCUMENTATION.md#troubleshooting).

---

## 📊 Project Statistics

- **Total Python files:** 33
- **Total Markdown files:** 11
- **Lines of code:** ~10,000+
- **Main components:** 4 (RAG, SQL, Forms, Frontend)
- **Available tools:** 2 (consult_legislation, get_institution_address)

---

## 📝 License

Academic project for consulting Romanian legislation.

---

## 🔗 References

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
