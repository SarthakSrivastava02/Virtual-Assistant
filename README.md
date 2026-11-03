# AI-Powered Virtual Assistant Using Large Language Models (LLM) & RAG

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![FAISS](https://img.shields.io/badge/Vector%20DB-FAISS-orange.svg)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

An advanced, full-stack, academic-grade conversational Virtual Assistant developed for **B.Tech Computer Science and Engineering** final-year / capstone project requirements.

The application combines state-of-the-art **Large Language Models (LLMs)**, **Retrieval-Augmented Generation (RAG)** using **FAISS vector database**, **LangChain orchestration**, **FastAPI asynchronous backend**, **SQLite persistent storage**, and a modern **React + Tailwind CSS** ChatGPT-inspired user interface.

---

## 📑 Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. System Architecture](#2-system-architecture)
- [3. Key Features](#3-key-features)
- [4. Technology Stack](#4-technology-stack)
- [5. Project Directory Structure](#5-project-directory-structure)
- [6. Installation & Execution Guide](#6-installation--execution-guide)
- [7. Configuration & API Key Setup](#7-configuration--api-key-setup)
- [8. Knowledge Assistant Mode (Study Notes)](#8-knowledge-assistant-mode-study-notes)
- [9. REST API Reference](#9-rest-api-reference)
- [10. Academic Evaluation & Test Queries](#10-academic-evaluation--test-queries)
- [11. Hardware Requirements & Optimization](#11-hardware-requirements--optimization)
- [12. Security & Reliability](#12-security--reliability)
- [13. Future Enhancements](#13-future-enhancements)

---

## 1. Project Overview

Modern conversational AI systems often suffer from two major limitations:
1. **Hallucinations & Knowledge Obsolescence:** LLMs do not know about personal, enterprise, or newly uploaded course lecture notes.
2. **Lack of Integrated Tools:** Standard chatbots cannot reliably evaluate complex mathematical equations without error, track persistent to-do tasks, or generate exact bibliographic citations.

This project solves these limitations by implementing a **modular, multi-tier Virtual Assistant** that combines:
- **Retrieval-Augmented Generation (RAG):** Extracts, chunks, and semantically indexes user PDFs, TXT, and Markdown documents using dense vector embeddings in FAISS, allowing students to query their course materials with verified source citations.
- **Multi-LLM Support:** Native compatibility with OpenAI API (`gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`), Local LLaMA via Ollama (`llama3`, `mistral`), and a built-in Academic Simulation Engine that operates completely offline without API keys.
- **Safe Task Executors:** Mathematical parser evaluated strictly via Abstract Syntax Tree (AST) inspection to prevent arbitrary code execution, real-time date/time tools, extractive summarizers, and an integrated SQLite task manager.

---

## 2. System Architecture

```text
                               +----------------------------------------+
                               |              USER BROWSER              |
                               |  React.js + Tailwind CSS UI (Port 8000)|
                               +-------------------+--------------------+
                                                   | HTTP / REST
                                                   v
                               +----------------------------------------+
                               |             FASTAPI SERVER             |
                               |            (Asynchronous)              |
                               +-------------------+--------------------+
                                                   |
                   +-------------------------------+-------------------------------+
                   |                               |                               |
                   v                               v                               v
         [Request Processing]             [Document Ingestion]            [Conversation History]
                   |                               |                               |
                   v                               v                               v
        [Intent Classification]          [Text Extractor: PyPDF]           [SQLite Database]
        - calculation                              |                         - conversations
        - datetime                                 v                         - messages
        - todo                           [Overlapping Chunking]              - documents
        - summarize                                |                         - chunks
        - general / rag                            v                         - todos
                   |                     [Embedding Engine]
                   v                     - SentenceTransformers
         [Execution Routing]             - TF-IDF / Cosine fallback
         /                 \                       |
        /                   \                      v
       v                     v             [FAISS Vector Store]
[Safe Tool Engine]    [RAG Retrieval]     - Cosine similarity
- AST Calculator      - Top-K Chunks      - Metadata mapping
- DateTime Tool       - Confidence score           |
- SQLite Todos        - Page numbers               |
       \                     \                     /
        \                     v                   v
         \---------> [LangChain LLM Orchestration] <---------/
                                   |
             +---------------------+---------------------+
             |                     |                     |
             v                     v                     v
      [OpenAI API]         [Local LLaMA]       [Academic Fallback]
      (gpt-4o-mini)          (Ollama)             (Offline CS KB)
             |                     |                     |
             +---------------------+---------------------+
                                   |
                                   v
                      [Context-Aware Response]
                      + Source Citations & Scores
                                   |
                                   v
                          [React Interface]
```

### RAG Ingestion & Query Workflow

1. **Document Ingestion:**
   - The user uploads a `.pdf`, `.txt`, or `.md` file.
   - Text is extracted page-by-page.
   - A recursive character chunking algorithm splits text into segments (default: 500 characters with 100-character overlap) preserving sentence boundaries.
   - Dense embeddings (384-dimensional vectors) are generated.
   - Vectors are indexed in FAISS (`IndexFlatIP`) or normalized NumPy Cosine Matrix.

2. **Query & Retrieval:**
   - When a user asks a question, the query vector is computed.
   - FAISS searches the index for the Top-K nearest chunks based on cosine similarity.
   - Chunks meeting the similarity threshold are structured into a grounded context window.

3. **Grounded Generation:**
   - The LLM receives the system prompt, conversation history (conversational memory), retrieved context snippets, and user query.
   - The assistant outputs the answer along with exact document citations (page number, chunk ID, relevance match %).

---

## 3. Key Features

- **💬 Intelligent Conversational Chat:** Natural language multi-turn dialog with context retention stored in SQLite.
- **📚 Knowledge Assistant Mode (Study Notes):** Dedicated hub to manage college notes, view document statistics (pages, chunks, size), generate 1-click summaries, and query specific files.
- **🧠 FAISS Vector RAG Engine:** Fast semantic search with strict mode ("Answer only from notes") and citation badges.
- **🧮 Safe Mathematical AST Calculator:** Evaluates arithmetic, powers, square roots, trigonometry, and logarithms without using `eval()`.
- **📅 Date, Time & Calendar Tools:** Instant access to formatted timestamps, days of the week, and calendar data.
- **📝 Integrated To-Do Manager:** Add, complete, and track study tasks via natural language or an interactive modal.
- **⚡ Dual Frontend Delivery:** Run out-of-the-box via FastAPI with zero npm setup, or run standard Vite dev server with `npm run dev`.
- **🌙 Dark & Light Mode:** Modern, ChatGPT-inspired UI with smooth transitions and full mobile responsiveness.

---

## 4. Technology Stack

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Frontend** | React 18 | Declarative reactive UI components |
| | Tailwind CSS | Utility-first responsive design & dark mode |
| | Lucide Icons | Clean SVG typography and interface icons |
| | Vite 5 | Modern fast frontend tooling |
| **Backend** | Python 3.10+ | High-performance backend runtime |
| | FastAPI | Modern asynchronous ASGI web framework |
| | Uvicorn | High-throughput ASGI production server |
| | Pydantic v2 | Robust data validation and JSON serialization |
| | SQLite 3 | Relational database with foreign key cascades |
| **AI / LLM** | LangChain | LLM orchestration and prompt templating |
| | OpenAI API | Cloud LLM integration (`gpt-4o-mini`, `gpt-4o`) |
| | Ollama / LLaMA | Local private offline LLM compatibility |
| **Vector DB**| FAISS | Facebook AI Similarity Search vector index |
| | SentenceTransformers| Hugging Face `all-MiniLM-L6-v2` dense embeddings |
| | Scikit-Learn | High-efficiency TF-IDF and Cosine fallbacks |
| **Documents**| PyPDF | Native PDF text and page extraction |

---

## 5. Project Directory Structure

```text
Virtual Assistant/
├── backend/
│   ├── main.py                 # FastAPI application, routing, and static mounting
│   ├── llm_service.py          # Multi-provider LLM orchestration & LangChain prompts
│   ├── rag_service.py          # FAISS vector store & embedding engine
│   ├── document_processor.py   # PDF/TXT extraction, sanitization, and text chunker
│   ├── task_executor.py        # Safe AST calculator, DateTime tool, and To-Do manager
│   ├── database.py             # SQLite database connections, schema, and CRUD
│   ├── models.py               # Pydantic validation schemas
│   ├── config.py               # Environment variables and application settings
│   ├── requirements.txt        # Python backend dependencies
│   └── .env.example            # Environment configuration template
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx             # Chat history, new chat, theme switcher
│   │   │   ├── ChatWindow.jsx          # Header, message stream, auto-scroll
│   │   │   ├── MessageBubble.jsx       # Markdown styling & RAG citation badges
│   │   │   ├── ChatInput.jsx           # Auto-resizing textarea, RAG toggle pills
│   │   │   ├── FileUpload.jsx          # Drag-and-drop ingestion modal
│   │   │   ├── WelcomeScreen.jsx       # Quick prompt cards and feature overview
│   │   │   ├── Settings.jsx            # API key & model configuration dialog
│   │   │   ├── KnowledgeAssistant.jsx  # College notes & study materials hub
│   │   │   └── TodoListModal.jsx       # SQLite task tracking interface
│   │   ├── App.jsx                     # Top-level state and API orchestration
│   │   ├── main.jsx                    # React DOM entry point
│   │   └── index.css                   # Custom scrollbars and Tailwind styles
│   ├── dist/
│   │   └── index.html                  # Standalone pre-bundled production UI
│   ├── package.json                    # Node dependencies and build scripts
│   ├── vite.config.js                  # Vite configuration and proxy rules
│   ├── tailwind.config.js              # Tailwind styling theme
│   └── index.html                      # HTML entry template
│
├── data/                               # Persistent runtime storage
│   ├── documents/                      # Uploaded PDFs and lecture notes
│   ├── faiss_index/                    # Serialized FAISS vector index & metadata
│   └── virtual_assistant.db            # SQLite relational database
│
├── sample_documents/                   # Ready-to-use study notes for evaluation
│   ├── operating_systems_notes.txt     # Concurrency, Paging, Deadlocks
│   └── artificial_intelligence_notes.txt # Search, Transformer equations, RAG
│
├── tests/
│   ├── test_backend.py                 # Unit tests for database, tools, and RAG
│   └── test_api_endpoints.py           # Integration tests for all 11 REST endpoints
│
├── run.py                              # Single-command launcher script
├── README.md                           # Comprehensive documentation
└── .gitignore                          # Git exclusion rules
```

---

## 6. Installation & Execution Guide

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14.
- 8 GB RAM standard laptop (no GPU needed).
- (Optional) Node.js 18+ if you want to run Vite dev mode.

---

### Step 1: Clone or Navigate to the Project

```bash
cd "Virtual Assistant"
```

### Step 2: Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate on macOS / Linux:
source venv/bin/activate

# (On Windows Command Prompt):
# venv\Scripts\activate.bat
```

### Step 3: Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

*(Note: All core modules include zero-dependency intelligent fallbacks, so the system operates even if platform-specific binary wheels are building).*

---

### Step 4: Run the Application (Single Command!)

You can start the full application with the single-command runner:

```bash
python3 run.py
```

Or run directly with Uvicorn:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Now open **`http://localhost:8000`** in any web browser. You will see the complete, interactive React interface!

---

### Step 5 (Optional): Run React in Vite Development Mode

If you wish to make changes to the React source code with Hot Module Replacement (HMR):

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server will run at `http://localhost:3000` and automatically proxies all API requests to FastAPI at `http://localhost:8000`.

---

## 7. Configuration & API Key Setup

Configuration is handled seamlessly through environment variables or directly inside the UI!

### Option A: Via the Web UI (Easiest)
1. Open `http://localhost:8000`.
2. Click the **⚙️ Settings** button in the sidebar.
3. Paste your OpenAI API Key (`sk-...`) and click **Save Settings**.
4. The key is securely stored in memory and masked in API responses.

### Option B: Via `.env` File
Create a `.env` file in the project root:

```bash
cp backend/.env.example .env
```

Edit `.env`:
```ini
OPENAI_API_KEY=sk-proj-your-actual-openai-key-here
OPENAI_MODEL=gpt-4o-mini
LLM_PROVIDER=auto
CHUNK_SIZE=500
CHUNK_OVERLAP=100
TOP_K_RESULTS=4
```

### Option C: Using Local LLaMA (Ollama)
1. Install [Ollama](https://ollama.com/) and pull a model:
   ```bash
   ollama pull llama3
   ```
2. In Settings, select **Local LLaMA** and set URL to `http://localhost:11434`.

### Option D: Smart Academic Offline Engine (Zero Keys Required!)
If you do not have an OpenAI API key or internet access, **leave the API key blank**. The assistant automatically uses its built-in Academic Simulation Engine. It will answer computer science questions, execute RAG retrieval with citations, evaluate math, and manage to-do tasks offline!

---

## 8. Knowledge Assistant Mode (Study Notes)

The **Knowledge Assistant Mode** is specifically built for students and researchers to interact with their study materials.

### How to Use:
1. Click **📚 Knowledge Mode** in the left sidebar.
2. Click **+ Upload New Document** or upload files from `sample_documents/`:
   - `operating_systems_notes.txt`
   - `artificial_intelligence_notes.txt`
3. View the document statistics: Page count, chunk count, file size.
4. Click **⚡ Summarize** to view an instant 5-point executive summary.
5. Click **💬 Ask Notes** to set document focus and ask specific questions.
6. The assistant responds with exact sentences and displays **📚 Referenced Sources** indicating page number and match confidence.

---

## 9. REST API Reference

The FastAPI backend exposes 11 interactive endpoints documented automatically via Swagger at `http://localhost:8000/docs`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/chat` | Main conversational endpoint with intent detection, RAG, and tools |
| `POST` | `/upload` | Ingests PDF/TXT, extracts text, chunks, and updates FAISS index |
| `GET` | `/history` | Lists all previous conversation sessions |
| `GET` | `/history/{conv_id}` | Retrieves full transcript and messages for a conversation |
| `POST` | `/new-chat` | Initializes a fresh conversation session |
| `DELETE` | `/clear-history` | Deletes all conversation logs and transcripts |
| `DELETE` | `/conversations/{id}` | Deletes a specific conversation session |
| `GET` | `/documents` | Lists all indexed documents in the knowledge base |
| `POST` | `/documents/{id}/summarize`| Generates an extractive summary of an uploaded document |
| `DELETE` | `/documents/{id}` | Deletes a document and rebuilds the vector index |
| `GET` | `/todos` | Lists all SQLite persistent to-do tasks |
| `POST` | `/todos` | Adds a new task item |
| `PUT` | `/todos/{id}` | Updates task completion status |
| `DELETE` | `/todos/{id}` | Deletes a to-do item |
| `GET` | `/settings` | Returns system configuration with masked API keys |
| `POST` | `/settings` | Updates runtime LLM provider and parameters |
| `GET` | `/health` | System health, indexed chunk counts, and database status |

---

## 10. Academic Evaluation & Test Queries

Use these sample questions during your academic demonstration:

### 1. Document RAG Retrieval Test
> *Prerequisite: Upload `sample_documents/operating_systems_notes.txt` first.*
- **Prompt:** `"What operations do semaphores provide according to the notes?"`
- **Expected Result:** Assistant quotes `wait()` (P) and `signal()` (V), explains binary vs counting semaphores, and displays a citation badge referencing `operating_systems_notes.txt` (Page 1).

### 2. Strict Notes Mode Test
- Toggle **🎯 Strict Notes Mode** on.
- **Prompt:** `"What is the capital of France?"`
- **Expected Result:** Assistant detects that the information is absent from the uploaded notes and answers: *"Based on the uploaded documents, this information is not mentioned."*

### 3. Safe Math Tool Test
- **Prompt:** `"calculate sqrt(144) * 5 + 10"`
- **Expected Result:** `Result: 70` (Evaluated via AST parsing).

### 4. Real-Time DateTime Test
- **Prompt:** `"What is today's date and the current time?"`
- **Expected Result:** Formatted day of week, month, date, year, and 12-hour/24-hour time.

### 5. Automated To-Do List Tool
- **Prompt:** `"add review Unit 3 concurrency to my todos"`
- **Expected Result:** `✅ Added to-do: review Unit 3 concurrency`.
- Check sidebar: The task badge increments and appears in the To-Do modal!

---

## 11. Hardware Requirements & Optimization

- **RAM:** Minimum 8 GB RAM. (Lightweight memory footprint: ~150 MB for backend).
- **CPU:** Standard Intel / AMD / Apple Silicon dual-core or quad-core processor.
- **Storage:** < 200 MB disk space.
- **No Dedicated GPU Required:** All inference is either cloud-routed (OpenAI) or executed via efficient CPU vector calculations.

---

## 12. Security & Reliability

1. **AST Math Validation:** Unlike naive implementations that use Python's dangerous `eval()`, the calculator parses the mathematical syntax tree and strictly disallows function calls, attribute access (`__import__`), loops, or system commands.
2. **File Sanitization:** Uploaded filenames are stripped of directory traversal tokens (`../`) to prevent arbitrary file overwrites.
3. **API Key Isolation:** API keys are managed server-side, never returned in plaintext to the frontend, and masked in configuration endpoints.
4. **CORS & Input Validation:** Pydantic schemas enforce type constraints, maximum sizes, and prevent malformed payloads.

---

## 13. Future Enhancements

- **Voice Input / Speech-to-Text (Whisper):** Direct audio transcription for speech-based academic questions.
- **Multi-Modal Document Vision:** Ingesting diagrams, flowcharts, and mathematical charts from PDFs via Vision LLMs.
- **Hierarchical RAG (Parent-Child Indexing):** Indexing small chunks for vector similarity and retrieving larger parent sections for generation context.
- **Automated Quiz Generation:** Generating multiple-choice questions from lecture notes for exam self-assessment.

---

## 👨‍💻 Academic Project Details

- **Project Title:** Building a Virtual Assistant Using Large Language Models (LLM) and Retrieval-Augmented Generation
- **Target Degree:** B.Tech / B.E. in Computer Science and Engineering
- **Domain:** Artificial Intelligence, Natural Language Processing, Full-Stack Web Development

---

## 📄 License

This project is licensed under the MIT License - open-source for academic, educational, and development purposes.
