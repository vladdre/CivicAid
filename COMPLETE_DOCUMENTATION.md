# 📚 CivicAID - Complete Consolidated Documentation

> **Intelligent Legal Assistant** - Functional cognitive system for consulting Romanian legislation and finding information about public institutions.

---

## 📋 Table of Contents

1. [General Overview](#general-overview)
2. [Complete Project Structure](#complete-project-structure)
3. [File Details](#file-details)
4. [Installation and Configuration](#installation-and-configuration)
5. [Usage](#usage)
6. [Technical Architecture](#technical-architecture)
7. [Main Components](#main-components)
8. [Optimizations](#optimizations)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 General Overview

CivicAID is an AI system that helps Romanian citizens to:
- **Consult legislation** using RAG (Retrieval-Augmented Generation)
- **Find public institutions** using Text-to-SQL
- **Generate official requests** (e.g.: ANPC) automatically
- **Interact naturally** through web chat or CLI

### Technologies Used

- **LangChain** - Framework for orchestrating AI
- **ChromaDB** - Vector database for RAG
- **OpenAI GPT-4o** - Language model for generation and embeddings
- **Flask** - Web framework for user interface
- **SQLite** - Database for institutions
- **SQLAlchemy** - ORM for SQL queries

---

## 📁 Complete Project Structure

```
CivicAID/
├── 📄 README.md                      # Main documentation
├── 📄 README_START.md                # Quick start guide
├── 📄 COMPLETE_DOCUMENTATION.md      # This file (consolidated documentation)
├── 📄 requirements.txt               # Python dependencies
├── 📄 .env                           # Environment variables (not versioned)
├── 📄 .gitignore                     # Files ignored by Git
│
├── 🚀 start_server.py                # Main automatic start script
├── 📝 main.py                        # CLI entry point
├── 🕷️ scrapper.py                   # Monitor Oficial scraper
├── 🔍 check_progress.py             # Scraper progress check
├── ✅ verify_extraction.py           # Data extraction verification
├── 🧪 test_scraper.py                # Tests for scraper
├── 📊 checkpoint.json                # Checkpoint for scraper
├── 📋 legi.json                      # Laws extracted from Monitor Oficial
│
├── 📂 app/                           # Main application code
│   ├── __init__.py
│   │
│   ├── 🤖 agent/                     # Cognitive agent (OpenAI Functions)
│   │   ├── __init__.py
│   │   ├── agent.py                  # Main agent logic
│   │   ├── agent_main.py            # CLI entry point for agent
│   │   ├── tools.py                  # Tool definitions for OpenAI Functions
│   │   └── README.md                 # Agent documentation
│   │
│   ├── 🧠 core/                      # Main functionalities
│   │   ├── __init__.py
│   │   └── query_processor.py       # Query processing (RAG + SQL)
│   │
│   ├── 🖥️ frontend/                  # Flask application
│   │   ├── __init__.py
│   │   ├── app.py                    # Main Flask application
│   │   ├── query_classifier.py      # Query classification
│   │   ├── title_generator.py       # Conversation title generation
│   │   ├── static/                   # Static files (CSS, JS, images)
│   │   │   ├── css/
│   │   │   ├── js/
│   │   │   └── images/
│   │   └── templates/               # HTML templates
│   │       ├── index.html
│   │       ├── login.html
│   │       └── register.html
│   │
│   ├── 🔧 scripts/                   # Utility scripts
│   │   ├── __init__.py
│   │   ├── find_law.py               # Search in vector store
│   │   ├── ingest_laws.py           # PDF ingestion into vector store
│   │   ├── ingest_json_laws.py      # legi.json ingestion into vector store
│   │   ├── setup_sql_db.py          # SQL database setup
│   │   ├── README_FIND_LAW.md       # find_law.py documentation
│   │   └── EXPLAIN_EMBEDDINGS.md    # Embeddings explanation
│   │
│   └── 🛠️ tools/                     # Tools
│       ├── __init__.py
│       ├── sql.py                    # Tool for SQL queries (Text-to-SQL)
│       └── anpc_form.py              # Tool for generating ANPC requests
│
├── 📂 data/                          # Data
│   ├── vector_store/                 # ChromaDB vector store (PDFs)
│   ├── vector_store_json/            # ChromaDB vector store (legi.json)
│   ├── raw_laws/                     # PDF files with laws (to be added manually)
│   ├── scraped_content/              # Raw text extracted from websites
│   ├── generated_forms/           # Generated forms
│   ├── chat.json                     # Conversations database
│   ├── users.json                    # Users database
│   ├── institutions.json             # Institutions data
│   ├── institutions.db               # SQLite database
│   ├── output.txt                    # Temporary output
│   ├── search_results.txt            # Search results
│   └── cerere_ANPC.txt               # Request templates
│
├── 📂 docs/                          # Documentation
│   ├── PROJECT_STRUCTURE.md          # Detailed project structure
│   ├── TASK_VERIFICATION.md         # Task verification
│   ├── STRUCTURE.md                  # Project structure
│   ├── SETUP.md                      # Setup guide
│   ├── OPTIMIZATIONS.md              # Implemented optimizations
│   └── TECHNICAL_SPECS.md            # Detailed technical specifications
│
├── 📂 tests/                         # Tests
│   ├── test_db.py                    # Database tests
│   ├── test_sql_tool.py             # SQL tool tests
│   ├── test_vector_store.py         # Vector store tests
│   ├── analyze_quality.py            # Quality analysis
│   └── debug_embeddings.py          # Embeddings debug
│
└── 📂 frontend/                      # Alternative frontend (legacy)
    └── frontend/
        └── app.py
```

---

## 📄 File Details

### 🚀 Root Files

#### `start_server.py`
**Purpose:** Main automatic start script that checks and configures all dependencies.

**Functionalities:**
- Checks existence of vector store (PDF and JSON)
- Creates vector store if it doesn't exist (runs `ingest_laws.py` and `ingest_json_laws.py`)
- Checks existence of SQL database
- Creates SQL database if it doesn't exist (runs `setup_sql_db.py`)
- Starts Flask server at `http://localhost:5000`

**Usage:**
```bash
python start_server.py
```

#### `main.py`
**Purpose:** Entry point for CLI (Command Line Interface).

**Functionalities:**
- Receives user message as argument
- Processes query using `process_query()`
- Displays result in console

**Usage:**
```bash
python main.py "Am fost implicat intr un accident auto. Celalalt sofer a plecta. Ce pot face?"
```

#### `scrapper.py`
**Purpose:** Scraper for Monitor Oficial - tracking law modifications.

**Functionalities:**
- Downloads PDF documents from Monitor Oficial
- Extracts text from PDFs using PyPDF2
- Identifies laws mentioned in documents
- Tracks last mention and last modification for each law
- Saves results in `legi.json`

**Usage:**
```bash
python scrapper.py
```

#### `check_progress.py`
**Purpose:** Scraper progress check.

#### `verify_extraction.py`
**Purpose:** Data extraction verification from scraper.

#### `test_scraper.py`
**Purpose:** Tests for scraper.

---

### 🤖 Agent (`app/agent/`)

#### `agent.py`
**Purpose:** Functional cognitive agent using OpenAI Functions Agent.

**Classes:**
- `Agent`: Main agent class

**Main methods:**
- `__init__(model, temperature)`: Initializes agent
- `chat(user_message)`: Simplified method for chat
- `process(user_message, max_iterations)`: Processes message using OpenAI Functions architecture
- `_execute_tool(tool_name, arguments)`: Executes a specified tool
- `add_to_history(role, content)`: Adds message to history
- `clear_history()`: Clears conversation history

**Architecture:**
1. Input: User Message
2. LLM Processing: GPT-4o analyzes input
3. Router (Decision): Decides which tool to use
4. Action: Executes selected tool
5. Observation: Receives result
6. Final Response: Synthesizes response

#### `agent_main.py`
**Purpose:** CLI entry point for agent.

**Modes:**
- **Interactive:** `python app/agent/agent_main.py`
- **CLI with message:** `python app/agent/agent_main.py "Your message"`

#### `tools.py`
**Purpose:** Tool definitions for OpenAI Functions.

**Available tools:**
1. `consult_legislation`: Consults Romanian legislation
2. `get_institution_address`: Finds public institution addresses

**Functions:**
- `consult_legislation(user_message, conversation_history)`: Consults legislation
- `get_institution_address(user_message, conversation_history)`: Finds institutions

**Definitions:**
- `TOOLS_DEFINITIONS`: List of tool definitions for OpenAI
- `TOOLS_MAP`: Function mapping for execution

---

### 🧠 Core (`app/core/`)

#### `query_processor.py`
**Purpose:** Main query processing (RAG + SQL + forms).

**Main functions:**
- `process_query(user_message, conversation_history, verbose, refresh_token, username)`: Main processing function
- `check_vector_store_exists()`: Checks vector store existence (with cache)
- `create_vector_store()`: Creates vector store by running `ingest_laws.py`
- `run_find_law(user_message, conversation_history, verbose)`: Runs search in vector store
- `summarize_results(results, user_query, conversation_history, verbose)`: Synthesizes results
- `is_summary_relevant(summary, user_query, api_key)`: Checks summary relevance
- `search_in_json_files(user_query, api_key, verbose)`: Searches in JSON vector store
- `write_output_to_file(output, output_file)`: Writes output to file (only for CLI)

**Processing flow:**
1. Checks if it's a form request
2. Checks/creates vector store
3. Runs `find_law.py` for semantic search
4. Generates synthesized summary
5. Checks summary relevance
6. Searches in JSON vector store as fallback
7. Returns final result

---

### 🖥️ Frontend (`app/frontend/`)

#### `app.py`
**Purpose:** Main Flask application for web interface.

**Routes:**
- `GET /`: Main page (chat interface)
- `GET /login`: Login page
- `POST /login`: Login processing
- `GET /register`: Registration page
- `POST /register`: Registration processing
- `GET /logout`: Logout
- `GET /api/conversations`: Gets conversation list
- `GET /api/conversations/<id>`: Gets messages from a conversation
- `POST /api/chat`: Processes user message
- `POST /api/voice-to-text`: Audio to text conversion
- `DELETE /api/conversations/<id>`: Deletes conversation
- `GET /auth/google`: Initiates OAuth flow for Gmail
- `GET /auth/google/callback`: Processes OAuth callback
- `GET /api/user/refresh-token`: Gets user refresh token

**Functionalities:**
- User authentication (login/register)
- Chat interface with conversation history
- Voice-to-text for vocal input
- Google OAuth for sending forms via email
- Session and conversation management

#### `query_classifier.py`
**Purpose:** Query classification to determine if database results are needed.

**Functions:**
- `needs_database_results(message, conversation_history)`: Determines if query needs SQL results

#### `title_generator.py`
**Purpose:** Title generation for conversations.

**Functions:**
- `generate_conversation_title(message)`: Generates conversation title using OpenAI

#### HTML Templates
- `index.html`: Main chat interface
- `login.html`: Login page
- `register.html`: Registration page

---

### 🔧 Scripts (`app/scripts/`)

#### `ingest_laws.py`
**Purpose:** Data Ingestion Pipeline for PDFs - creates vector store from PDFs.

**Functions:**
- `load_pdfs(raw_laws_dir)`: Loads PDFs from `data/raw_laws/`
- `split_documents(documents, chunk_size, chunk_overlap)`: Splits documents into chunks
- `create_vector_store(chunks, vector_store_dir)`: Creates embeddings and saves them in ChromaDB
- `main()`: Main pipeline execution

**Parameters:**
- `CHUNK_SIZE = 1000`: Chunk size
- `CHUNK_OVERLAP = 200`: Overlap between chunks

**Usage:**
```bash
python -m app.scripts.ingest_laws
```

#### `ingest_json_laws.py`
**Purpose:** Data Ingestion Pipeline for `legi.json` - creates vector store from JSON.

**Functions:**
- `load_json_laws(legi_json_path)`: Loads laws from `legi.json`
- `split_documents(documents, chunk_size, chunk_overlap)`: Splits documents into chunks
- `create_vector_store(chunks, vector_store_dir)`: Creates embeddings and saves them in ChromaDB
- `main()`: Main execution

**Usage:**
```bash
python -m app.scripts.ingest_json_laws
```

#### `find_law.py`
**Purpose:** Finding relevant law articles based on a message.

**Functions:**
- `extract_keywords_and_query(user_message, api_key, conversation_history, verbose)`: Optimizes query using LLM
- `find_relevant_laws(user_message, k, use_optimization, conversation_history, verbose)`: Finds relevant articles
- `format_results(results)`: Formats results for display
- `main()`: Main function (CLI)

**Parameters:**
- `k = 5`: Number of results returned
- `use_optimization = True`: Whether to optimize query

**Usage:**
```bash
python -m app.scripts.find_law "Am avut un accident de mașină"
```

#### `setup_sql_db.py`
**Purpose:** Creating and populating SQLite database with institutions.

**Functions:**
- `load_institutions_from_json(json_file)`: Loads data from `data/institutions.json`
- `create_database(db_file)`: Creates SQLite database
- `populate_database(session, institutions)`: Populates database
- `verify_database(session)`: Verifies database content
- `main()`: Main execution

**Table schema `institutions`:**
- `id`: Primary Key
- `nume`: Institution name
- `adresa`: Complete address
- `tip_serviciu`: Keywords about services
- `program`: Operating hours
- `grad_ocupare`: Information about crowding

**Usage:**
```bash
python -m app.scripts.setup_sql_db
```

---

### 🛠️ Tools (`app/tools/`)

#### `sql.py`
**Purpose:** Tool for SQL database queries using Text-to-SQL.

**Functions:**
- `get_api_key()`: Gets OpenAI API key from `.temp`, `.tmp` or `.env`
- `get_sql_database()`: Creates and returns SQLDatabase object
- `query_institutions(natural_language_query, vector_store_output, conversation_history)`: Transforms natural query to SQL and executes
- `format_sql_results(result)`: Formats SQL results
- `save_results_to_file(query, results, vector_store_output, sql_query)`: Saves results to file

**Usage:**
```python
from app.tools.sql import query_institutions
result = query_institutions("Unde găsesc case de pensii?")
```

#### `anpc_form.py`
**Purpose:** Tool for automatic generation of official requests (e.g.: ANPC).

**Functions:**
- `detect_form_request(message, conversation_history)`: Detects if message requests form generation
- `request_user_info()`: Returns message for requesting necessary information
- `extract_user_info_from_conversation(conversation_history, current_message)`: Extracts user information
- `complete_form_template(user_info, conversation_context)`: Completes request template
- `send_email_with_gmail_api(form_text, sender_email, recipient_email, refresh_token, user_name)`: Sends email via Gmail API
- `send_email_with_form(form_text, sender_email, recipient_email, user_name, refresh_token)`: Sends email (Gmail API or SMTP)
- `generate_anpc_form(user_message, conversation_history, refresh_token, username, verbose)`: Main function

**Usage:**
```python
from app.tools.anpc_form import generate_anpc_form
result = generate_anpc_form("Vreau să generez o cerere ANPC", conversation_history)
```

---

## 🔧 Installation and Configuration

### Prerequisites

- Python 3.10 or newer
- pip (Python package manager)
- OpenAI account with API key

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd CivicAID
```

### Step 2: Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Main dependencies:**
- `langchain`, `langchain-openai`, `langchain-community`, `langchain-text-splitters`, `langchain-core`
- `chromadb` - Vector database
- `pypdf`, `PyPDF2` - PDF processing
- `openai` - OpenAI SDK
- `flask` - Web framework
- `sqlalchemy` - ORM for SQL
- `python-dotenv` - Environment variables
- `reportlab` - PDF generation
- `google-auth`, `google-auth-oauthlib`, `google-api-python-client` - Google OAuth
- `SpeechRecognition`, `pyaudio`, `pydub` - Voice recognition
- `requests`, `beautifulsoup4`, `lxml` - Web scraping

### Step 4: Configure Environment Variables

Create `.env` file in project root:

```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Step 5: Prepare Data

1. **Add PDF files with laws:**
   ```bash
   mkdir -p data/raw_laws
   # Add PDFs to data/raw_laws/
   ```

2. **Add institution data:**
   ```bash
   # Create data/institutions.json with institution data
   ```

### Step 6: Start Server

```bash
python start_server.py
```

Script will:
- Check and create vector store if it doesn't exist
- Check and create SQL database if it doesn't exist
- Start Flask server at `http://localhost:5000`

---

## 🚀 Usage

### Web Server (Recommended)

```bash
python start_server.py
```

Then open `http://localhost:5000` in browser.

---

## 🏗️ Technical Architecture

### Data Flow (ETL)

#### 1. Initial Setup

```
PDFs → data/raw_laws/
         ↓
    ingest_laws.py
         ↓
    data/vector_store/ (laws)

legi.json
         ↓
    ingest_json_laws.py
         ↓
    data/vector_store_json/ (JSON laws)

institutions.json
         ↓
    setup_sql_db.py
         ↓
    data/institutions.db
```

#### 2. Runtime (User asks)

```
User Query
    ↓
query_processor.py
    ↓
    ├─→ Check if it's a form?
    │       ↓
    │   anpc_form.py → Generate and send request
    │
    ├─→ Needs legislation?
    │       ↓
    │   find_law.py → Vector Store (PDF/JSON) → Summary
    │
    └─→ Needs institutions?
            ↓
        sql.py → Text-to-SQL → institutions.db → Results
```

### Agent Architecture

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
    └─→ Direct Response (simple conversation)
    ↓
Synthesize Response
    ↓
User Response
```

---

## 🧩 Main Components

### 1. Vector Store (RAG)

**Technology:** ChromaDB with OpenAI Embeddings

**Process:**
1. **Load:** PDFs/JSON → Text (PyPDFLoader)
2. **Split:** Text → Chunks (RecursiveCharacterTextSplitter, size=1000, overlap=200)
3. **Embed:** Chunks → Vectors (OpenAIEmbeddings, text-embedding-3-small)
4. **Store:** Vectors → ChromaDB

**Search:**
- Query → Embedding → Similarity Search → Top K chunks → Summary

### 2. SQL Database (Text-to-SQL)

**Technology:** SQLite + SQLAlchemy + LangChain SQLDatabase

**Process:**
1. Natural language query
2. LLM generates SQL query
3. Executes on SQLite
4. Formats results

### 3. Form Generator

**Technology:** OpenAI GPT-4o + Gmail API / SMTP

**Process:**
1. Detects form request
2. Extracts user information
3. Completes template using AI
4. Sends email via Gmail API or SMTP

### 4. Web Frontend

**Technology:** Flask + HTML/CSS/JavaScript

**Functionalities:**
- User authentication
- Chat interface with history
- Voice-to-text (optional)
- Google OAuth for email
- Conversation management

---

## ⚡ Optimizations

### Implemented ✅

1. **File writing eliminated for API calls** - Latency reduction
2. **Print statements optimized** - `verbose` parameter (default: False)
3. **Asynchronous title generation** - No longer blocks response
4. **Vector store cache** - Avoids redundant checks
5. **Lazy loading vector store** - Reuses instance
6. **Optimized Web Scraping** - Filter total number of data (Binary search and last among equal indices)

### Possible (Future)

1. Parallel OpenAI calls (asyncio)
2. Caching for similar results
3. Database connection pooling

---

## 🔍 Troubleshooting

### Error: "OPENAI_API_KEY not found"

**Solution:**
1. Check that you created `.env` file in project root
2. Check that it contains exactly: `OPENAI_API_KEY=sk-proj-...`
3. Check that there are no spaces around `=`

### Error: "Vector store does not exist"

**Solution:**
```bash
python -m app.scripts.ingest_laws
```

### Error: "No module named 'langchain'"

**Solution:**
```bash
pip install -r requirements.txt
```

### Doesn't find relevant results

**Possible causes:**
- PDFs don't contain relevant information
- Vector store hasn't been updated
- Message is too general

**Solution:**
- Check what PDF/JSON you have in `data/raw_laws/`
- Run `ingest_laws.py` again to reindex
- Try to rephrase the message

### Error: "SQL database does not exist"

**Solution:**
```bash
python -m app.scripts.setup_sql_db
```

### Flask server doesn't start

**Solution:**
- Check that port 5000 is not already in use
- Check that all dependencies are installed
- Check logs for errors

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
