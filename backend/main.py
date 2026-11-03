import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
import database
from models import (
    UserRegister, UserLogin, UserProfile, AuthResponse,
    ChatRequest, ChatResponse, SourceCitation,
    ConversationSummary, ConversationDetail, NewChatResponse,
    DocumentUploadResponse, DocumentModel, DocumentSummaryResponse,
    TaskRequest, TaskResponse, TodoItem, TodoCreate, TodoUpdate,
    HealthResponse, SettingsUpdate
)
from document_processor import DocumentProcessor
from rag_service import rag_service
from task_executor import task_executor, IntentDetector, TextTools
from llm_service import llm_service

# Initialize FastAPI Application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="A modern, production-grade Virtual Assistant powered by LLMs, LangChain, FAISS, and RAG."
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application Lifecycle
@app.on_event("startup")
def on_startup():
    print("[Main] Initializing SQLite database...")
    database.init_db()
    print("[Main] System initialized successfully.")


# --- Authentication Endpoints ---

@app.post("/auth/register", response_model=AuthResponse, tags=["Authentication"])
def register(user_data: UserRegister):
    """Registers a new user account."""
    user = database.create_user(
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name
    )
    if not user:
        raise HTTPException(status_code=400, detail="Username is already taken.")
    
    # Generate token
    token = f"token_{user['id']}_{uuid.uuid4().hex[:12]}"
    return AuthResponse(
        success=True,
        token=token,
        user=UserProfile(
            id=user["id"],
            username=user["username"],
            full_name=user["full_name"],
            created_at=user["created_at"]
        ),
        message="Registration successful."
    )

@app.post("/auth/login", response_model=AuthResponse, tags=["Authentication"])
def login(creds: UserLogin):
    """Authenticates an existing user."""
    user = database.authenticate_user(username=creds.username, password=creds.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    
    token = f"token_{user['id']}_{uuid.uuid4().hex[:12]}"
    return AuthResponse(
        success=True,
        token=token,
        user=UserProfile(
            id=user["id"],
            username=user["username"],
            full_name=user["full_name"],
            created_at=user["created_at"]
        ),
        message="Login successful."
    )

@app.get("/auth/me", response_model=UserProfile, tags=["Authentication"])
def get_current_user(authorization: Optional[str] = Header(None)):
    """Verifies token and returns profile."""
    if not authorization or not authorization.startswith("Bearer "):
        # Return default guest/admin profile
        user = database.get_user_by_id(1)
        if user:
            return UserProfile(
                id=user["id"],
                username=user["username"],
                full_name=user["full_name"],
                created_at=user["created_at"]
            )
        raise HTTPException(status_code=401, detail="Authentication required.")

    token = authorization.replace("Bearer ", "").strip()
    try:
        parts = token.split("_")
        user_id = int(parts[1])
        user = database.get_user_by_id(user_id)
        if user:
            return UserProfile(
                id=user["id"],
                username=user["username"],
                full_name=user["full_name"],
                created_at=user["created_at"]
            )
    except Exception:
        pass
    raise HTTPException(status_code=401, detail="Invalid authentication token.")


# --- Health & Diagnostic Endpoints ---

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Returns system diagnostic status, indexing statistics, and active configuration."""
    docs = database.get_documents()
    convs = database.get_conversations()
    stats = rag_service.get_stats()
    return HealthResponse(
        status="healthy",
        version=settings.version,
        llm_provider=llm_service.provider,
        available_providers=["gemini", "openai", "local_llama", "auto"],
        documents_count=len(docs),
        total_chunks=stats["total_chunks_indexed"],
        conversations_count=len(convs),
        database_ok=True
    )


# --- Chat & Conversational Endpoints ---

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat_endpoint(request: ChatRequest):
    """
    Main conversational endpoint:
    1. Validates or initializes conversation session.
    2. Classifies user intent (calculation, datetime, todo, rag, general).
    3. Executes relevant task tools or retrieves semantic chunks from FAISS.
    4. Generates contextual response via LLM service.
    5. Stores conversation turns in SQLite.
    """
    user_msg = request.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # 1. Manage Conversation Session
    conv_id = request.conversation_id
    user_id = request.user_id or 1
    if not conv_id:
        conv_id = database.create_conversation(title=user_msg[:30] + ("..." if len(user_msg) > 30 else ""), user_id=user_id)
    else:
        existing = database.get_conversation(conv_id)
        if not existing:
            conv_id = database.create_conversation(title=user_msg[:30], conv_id=conv_id, user_id=user_id)

    # 2. Record User Message
    database.add_message(conv_id=conv_id, role="user", content=user_msg)

    # 3. Detect Intent
    intent = IntentDetector.detect_intent(user_msg)
    task_result = None
    sources_to_return: List[SourceCitation] = []
    assistant_reply = ""

    # 4. Route Execution Based on Intent & RAG Settings
    if intent in ["calculation", "datetime", "todo"]:
        task_res = task_executor.execute(intent=intent, message=user_msg)
        if task_res.get("success", False):
            task_result = task_res
            assistant_reply = task_res.get("message", "Task completed.")
        else:
            # Fall through to LLM for accurate conversational answers
            intent = "general"

    if not assistant_reply:
        # Knowledge Retrieval (RAG) check
        retrieved = []
        if request.use_rag:
            retrieved = rag_service.search(
                query=user_msg,
                top_k=settings.top_k_results,
                document_id=request.document_id
            )
            for r in retrieved:
                sources_to_return.append(SourceCitation(
                    document_id=r.get("document_id"),
                    document_name=r.get("document_name", "Document"),
                    chunk_id=r.get("chunk_id", 0),
                    page_number=r.get("page_number", 1),
                    relevance_score=r.get("relevance_score", 0.0),
                    snippet=r.get("snippet", "")
                ))

        # Check for strict RAG mode
        mode = "study_notes" if request.document_id is not None else "general"
        assistant_reply = llm_service.generate_response(
            user_message=user_msg,
            conversation_id=conv_id,
            retrieved_sources=retrieved,
            strict_rag=request.strict_rag,
            mode=mode
        )

    # 5. Persist Assistant Response
    serialized_sources = [s.model_dump() for s in sources_to_return] if sources_to_return else None
    msg_id = database.add_message(
        conv_id=conv_id,
        role="assistant",
        content=assistant_reply,
        sources=serialized_sources
    )

    return ChatResponse(
        response=assistant_reply,
        conversation_id=conv_id,
        message_id=msg_id,
        role="assistant",
        intent=intent,
        sources=sources_to_return,
        task_result=task_result,
        timestamp=datetime.now().isoformat()
    )


# --- Conversation History Management ---

@app.get("/history", response_model=List[ConversationSummary], tags=["History"])
def get_all_conversations(user_id: Optional[int] = Query(None)):
    """Lists all active and previous conversation sessions."""
    return database.get_conversations(user_id=user_id)

@app.get("/history/{conv_id}", response_model=ConversationDetail, tags=["History"])
def get_conversation_details(conv_id: str):
    """Retrieves full transcript and messages for a specific conversation."""
    conv = database.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv

@app.post("/new-chat", response_model=NewChatResponse, tags=["History"])
def create_new_chat(title: Optional[str] = "New Conversation", user_id: Optional[int] = Query(1)):
    """Spawns a fresh conversation session."""
    conv_id = database.create_conversation(title=title, user_id=user_id or 1)
    return NewChatResponse(
        conversation_id=conv_id,
        title=title,
        created_at=datetime.now().isoformat()
    )

@app.delete("/clear-history", tags=["History"])
def clear_history(user_id: Optional[int] = Query(None)):
    """Clears conversation transcripts and message logs from SQLite."""
    count = database.clear_all_conversations(user_id=user_id)
    return {"success": True, "message": f"Successfully cleared {count} conversations."}

@app.delete("/conversations/{conv_id}", tags=["History"])
def delete_single_conversation(conv_id: str):
    """Deletes an individual conversation by ID."""
    deleted = database.delete_conversation(conv_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "message": f"Deleted conversation {conv_id}."}


# --- Document Ingestion & RAG Endpoints ---

@app.post("/upload", response_model=DocumentUploadResponse, tags=["Documents & RAG"])
async def upload_document(file: UploadFile = File(...)):
    """
    RAG Ingestion Pipeline:
    1. Validates file format (.pdf, .txt, .md).
    2. Saves file to data/documents/.
    3. Extracts text and pages.
    4. Segments text into overlapping semantic chunks.
    5. Stores records in SQLite.
    6. Generates vector embeddings and updates the FAISS/NumPy index.
    """
    if not DocumentProcessor.is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension. Allowed formats: {', '.join(settings.allowed_extensions)}"
        )

    clean_filename = DocumentProcessor.sanitize_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex[:8]}_{clean_filename}"
    file_path = Path(settings.documents_dir) / unique_filename

    # Save uploaded bytes safely
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file to disk: {e}")

    file_size = os.path.getsize(file_path)

    # Extract text and chunk
    try:
        full_text, pages = DocumentProcessor.extract_text_from_file(str(file_path))
        chunks = DocumentProcessor.chunk_document(pages)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not extract readable text from uploaded file.")

        # Persist document metadata and chunks into SQLite
        doc_id = database.add_document(
            filename=clean_filename,
            file_type=Path(clean_filename).suffix.lower(),
            file_path=str(file_path),
            file_size=file_size,
            chunk_count=len(chunks),
            page_count=len(pages)
        )
        database.add_document_chunks(doc_id, chunks)

        # Update vector index
        rag_service.add_document(doc_id, clean_filename, chunks)

        return DocumentUploadResponse(
            success=True,
            document_id=doc_id,
            filename=clean_filename,
            chunks_created=len(chunks),
            page_count=len(pages),
            message=f"Indexed '{clean_filename}' ({len(chunks)} chunks, {len(pages)} page(s))."
        )
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.get("/documents", response_model=List[DocumentModel], tags=["Documents & RAG"])
def list_documents():
    """Lists all uploaded documents stored in the knowledge base."""
    return database.get_documents()

@app.get("/documents/{doc_id}", tags=["Documents & RAG"])
def get_document_details(doc_id: int):
    """Retrieves document metadata along with all indexed text chunks."""
    doc = database.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    chunks = database.get_document_chunks(doc_id)
    return {"document": doc, "chunks": chunks}

@app.post("/documents/{doc_id}/summarize", response_model=DocumentSummaryResponse, tags=["Documents & RAG"])
def summarize_document(doc_id: int):
    """Generates an extractive and key-takeaway summary of an entire uploaded document."""
    doc = database.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunks = database.get_document_chunks(doc_id)
    combined_text = "\n".join([c["content"] for c in chunks[:12]])
    summary_data = TextTools.extractive_summary(combined_text, num_sentences=5)

    return DocumentSummaryResponse(
        document_id=doc_id,
        filename=doc["filename"],
        summary=summary_data["summary"],
        key_points=summary_data["key_points"]
    )

@app.delete("/documents/{doc_id}", tags=["Documents & RAG"])
def delete_document_endpoint(doc_id: int):
    """Removes a document from the database and rebuilds the vector index."""
    doc = database.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove physical file
    if os.path.exists(doc["file_path"]):
        try:
            os.remove(doc["file_path"])
        except Exception:
            pass

    database.delete_document(doc_id)
    rag_service.remove_document(doc_id)
    return {"success": True, "message": f"Document '{doc['filename']}' deleted successfully."}


# --- Tool Execution & To-Do Endpoints ---

@app.post("/tasks/execute", response_model=TaskResponse, tags=["Tasks & Tools"])
def execute_task(req: TaskRequest):
    """Directly triggers task executors (math calculation, text summarization, tone rewrite, datetime)."""
    res = task_executor.execute(req.task_type, req.input_text or "", req.parameters)
    return TaskResponse(
        task_type=req.task_type,
        success=res.get("success", True),
        result=res.get("result"),
        message=res.get("message")
    )

@app.get("/todos", response_model=List[TodoItem], tags=["Tasks & Tools"])
def list_todos():
    """Lists all user to-do tasks."""
    return database.get_todos()

@app.post("/todos", response_model=TodoItem, tags=["Tasks & Tools"])
def add_todo(item: TodoCreate):
    """Creates a new to-do task item."""
    if not item.task.strip():
        raise HTTPException(status_code=400, detail="Task text cannot be empty.")
    todo_id = database.add_todo(item.task.strip())
    todos = database.get_todos()
    for t in todos:
        if t["id"] == todo_id:
            return t
    raise HTTPException(status_code=500, detail="Failed to retrieve created to-do item.")

@app.put("/todos/{todo_id}", tags=["Tasks & Tools"])
def update_todo_item(todo_id: int, update: TodoUpdate):
    """Updates completion status or task text."""
    success = database.update_todo(todo_id, completed=update.completed, task=update.task)
    if not success:
        raise HTTPException(status_code=404, detail="To-do item not found.")
    return {"success": True, "message": "Updated to-do item."}

@app.delete("/todos/{todo_id}", tags=["Tasks & Tools"])
def delete_todo_item(todo_id: int):
    """Deletes a to-do item by ID."""
    success = database.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="To-do item not found.")
    return {"success": True, "message": f"Deleted to-do item {todo_id}."}


# --- Settings & Configuration ---

@app.get("/settings", tags=["Settings"])
def get_settings():
    """Retrieves current application settings with masked API keys."""
    masked_gemini = ""
    if settings.gemini_api_key:
        masked_gemini = settings.gemini_api_key[:6] + "..." + settings.gemini_api_key[-4:]
    masked_openai = ""
    if settings.openai_api_key:
        masked_openai = settings.openai_api_key[:7] + "..." + settings.openai_api_key[-4:]
    return {
        "gemini_api_key_set": bool(settings.gemini_api_key),
        "gemini_api_key_masked": masked_gemini,
        "gemini_model": settings.gemini_model,
        "openai_api_key_set": bool(settings.openai_api_key),
        "openai_api_key_masked": masked_openai,
        "openai_model": settings.openai_model,
        "local_llm_url": settings.local_llm_url,
        "local_llm_model": settings.local_llm_model,
        "llm_provider": llm_service.provider,
        "chunk_size": settings.chunk_size,
        "top_k_results": settings.top_k_results
    }

@app.post("/settings", tags=["Settings"])
def update_settings(update: SettingsUpdate):
    """Updates runtime configuration for LLM provider, models, and API keys."""
    if update.gemini_api_key is not None or update.gemini_model is not None:
        llm_service.update_settings(
            gemini_key=update.gemini_api_key,
            gemini_model=update.gemini_model,
            openai_key=update.openai_api_key,
            openai_model=update.openai_model,
            provider=update.llm_provider
        )
    elif update.openai_api_key is not None:
        llm_service.update_settings(
            openai_key=update.openai_api_key,
            model=update.openai_model,
            provider=update.llm_provider
        )
    if update.openai_model is not None:
        settings.openai_model = update.openai_model
    if update.local_llm_url is not None:
        settings.local_llm_url = update.local_llm_url
    if update.local_llm_model is not None:
        settings.local_llm_model = update.local_llm_model
    if update.chunk_size is not None:
        settings.chunk_size = update.chunk_size
    if update.top_k_results is not None:
        settings.top_k_results = update.top_k_results

    return {"success": True, "message": "Settings updated successfully."}


# --- Static Frontend Mounting ---
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        file_target = frontend_dist / full_path
        if file_target.exists() and file_target.is_file():
            return FileResponse(file_target)
        return FileResponse(frontend_dist / "index.html")

if __name__ == "__main__":
    import uvicorn
    print(f"Starting {settings.app_name} on http://{settings.host}:{settings.port}")
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
