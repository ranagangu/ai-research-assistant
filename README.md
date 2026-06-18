# AI Research Assistant with RAG & LangGraph

A production-ready AI Research Assistant that allows users to upload documents (PDF, DOCX, TXT), index them in a local ChromaDB vector database, and perform context-aware research query interactions (RAG). The project features JWT security, chat session tracking, Server-Sent Events (SSE) token streaming, inline citation mapping, and an administration dashboard.

The retrieval and validation pipeline is orchestrated using **LangGraph** to construct a highly reliable agent workflow that checks for query intent, validates retrieved document relevance, and runs anti-hallucination validation checks.

---

## Technical Architecture

```
                                  +-----------------------+
                                  |     React Frontend    |
                                  |    (Tailwind, SSE)    |
                                  +-----------+-----------+
                                              | JWT HTTP / SSE
                                              v
                                  +-----------+-----------+
                                  |    FastAPI Backend    |
                                  |  (Routers, Middleware)|
                                  +-----------+-----------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
         +-----------+-----------+                         +-----------+-----------+
         |     SQLite Database   |                         |   LangGraph Agent     |
         | (Users, Docs, Chat)   |                         |  (Workflow Engine)    |
         +-----------------------+                         +-----------+-----------+
                                                                       |
                                             +-------------------------+-------------------------+
                                             |                         |                         |
                                             v                         v                         v
                                 +-----------+-----------+ +-----------+-----------+ +-----------+-----------+
                                 |       ChromaDB        | |     OpenAI LLM        | |    Google Gemini LLM    |
                                 |    (Vector Store)     | |  (gpt-4o-mini, etc.)  | |  (gemini-1.5-flash)   |
                                 +-----------------------+ +-----------------------+ +-----------------------+
```

### LangGraph Ingestion & Query Lifecycle
1. **Ingestion**: Documents uploaded by the user are parsed (via PyPDF, python-docx, or raw readers), chunked with `RecursiveCharacterTextSplitter` (1000 chars, 200 overlap), embedded using either OpenAI or Google Gemini embeddings, and stored in ChromaDB.
2. **Orchestration Workflow**:
   - **Query Analysis**: Evaluates query text against chat history, optimizes search terms, and decides if retrieval is necessary.
   - **Document Retrieval**: Searches ChromaDB using metadata tags filtering by user ID.
   - **Context Evaluation**: Grades retrieved text chunks for query relevance and filters out noise.
   - **Answer Generation**: Synthesizes a response using prompt contexts, inline citations, and chat memory history.
   - **Answer Validation**: Double-checks the generated text against context to evaluate for hallucinations (groundedness checks) and verifies if the user's question has been answered. If validation fails, it triggers a rewrite iteration (up to 2 attempts).

---

## Folder Structure

```
project/
│
├── backend/
│   ├── api/             # Routes and version configuration (mounts routes/)
│   ├── routes/          # REST endpoints (auth, chat, documents, admin)
│   ├── services/        # Business logic services (AI, document processor, vector store)
│   ├── chains/          # LangChain template definitions
│   ├── agents/          # Custom RAG LLM configurations
│   ├── graph/           # LangGraph configuration (workflow, state)
│   ├── models/          # SQLAlchemy db models & Pydantic schema models
│   ├── database/        # DB configuration (engine, session local)
│   ├── vectorstore/     # ChromaDB instance configuration
│   ├── utils/           # Utility helpers (security dependencies)
│   ├── uploads/         # Local disk storage for uploaded documents
│   ├── config/          # Project configurations (settings, dotenv loader)
│   ├── main.py          # FastAPI application startup script
│   └── test_api.py      # SQLite, JWT, and cascading DB tests
│
├── frontend/
│   ├── src/
│   │   ├── components/  # Chat interface, Document panel, Admin boards
│   │   ├── pages/       # Login, Register, Dashboard layouts
│   │   ├── services/    # Axios HTTP endpoints mappings
│   │   ├── context/     # Auth Context provider
│   │   ├── index.css    # Tailwind styling and glassmorphism classes
│   │   └── main.jsx     # Root mount file
│   ├── tailwind.config.js
│   └── package.json
│
├── docs/
│   └── api_docs.md      # API request & response schemas
│
├── requirements.txt     # Python backend dependencies
└── README.md            # Comprehensive project overview
```

---

## Installation & Setup

### Prerequisites
- Python 3.12+
- Node.js (v18+ recommended)
- OpenAI API Key and/or Google Gemini API Key

### 1. Configuration Setup
Create a `.env` file in the project root directory (you can copy the provided `.env.example` as a template):
```bash
# General Project Settings
PROJECT_NAME="AI Research Assistant"
SECRET_KEY="your-custom-very-long-random-secret-key"
DATABASE_URL="sqlite:///./research_assistant.db"
CHROMA_DB_DIR="./chroma_db"
UPLOAD_DIR="./uploads"

# AI Model Configuration (openai OR gemini)
DEFAULT_LLM_PROVIDER="gemini"
DEFAULT_LLM_MODEL="gemini-1.5-flash"
DEFAULT_EMBEDDING_PROVIDER="gemini"
DEFAULT_EMBEDDING_MODEL="models/text-embedding-004"

# API Keys (Provide at least one)
OPENAI_API_KEY="your-openai-api-key"
GEMINI_API_KEY="your-gemini-api-key"
```

### 2. Backend Setup
Set up a Python virtual environment, activate it, and install dependencies:
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On macOS/Linux: source venv/bin/activate

# Install requirements
pip install -r requirements.txt
pip install email-validator
```

### 3. Frontend Setup
Navigate to the frontend folder and install npm packages:
```bash
cd frontend
npm install
```

---

## Running the Application

### Start the Backend Server
From the root directory, with virtual environment activated:
```bash
python backend/main.py
```
*The server will start running on **`http://localhost:8000`**. You can verify and interact with the endpoints using the Swagger interface at `http://localhost:8000/docs`.*

### Start the Frontend Dev Server
In a new terminal window, navigate to the frontend folder and start the dev server:
```bash
cd frontend
npm run dev
```
*The app will start running on **`http://localhost:5173`**.*

---

## Running Automated Tests

A unit test suite validates JWT encoding, SQLite database integrity, user registration hash checks, and cascading relationship deletes. Run the following command in the project root:
```bash
python backend/test_api.py
```
All tests should return `OK`.
