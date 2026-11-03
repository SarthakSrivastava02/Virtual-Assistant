from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Authentication Models ---

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)
    full_name: Optional[str] = "User"

class UserLogin(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    id: int
    username: str
    full_name: str
    created_at: str

class AuthResponse(BaseModel):
    success: bool
    token: str
    user: UserProfile
    message: str

# --- Chat & Messaging Models ---

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user query or message")
    conversation_id: Optional[str] = Field(None, description="Active conversation UUID")
    use_rag: bool = Field(True, description="Whether to query the vector knowledge base")
    document_id: Optional[int] = Field(None, description="Optionally restrict retrieval to a specific document")
    strict_rag: bool = Field(False, description="Strict mode: only answer from uploaded documents")
    user_id: Optional[int] = Field(None, description="Current logged in user ID")

class SourceCitation(BaseModel):
    document_id: Optional[int] = None
    document_name: str
    chunk_id: int
    page_number: Optional[int] = 1
    relevance_score: float
    snippet: str

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: int
    role: str = "assistant"
    intent: str = "general"
    sources: List[SourceCitation] = []
    task_result: Optional[Dict[str, Any]] = None
    timestamp: str

# --- Conversation & History Models ---

class MessageModel(BaseModel):
    id: int
    conversation_id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: str

class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[MessageModel]

class NewChatResponse(BaseModel):
    conversation_id: str
    title: str
    created_at: str

# --- Document & Knowledge Base Models ---

class DocumentModel(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size_bytes: int
    chunk_count: int
    page_count: int
    uploaded_at: str

class DocumentUploadResponse(BaseModel):
    success: bool
    document_id: int
    filename: str
    chunks_created: int
    page_count: int
    message: str

class DocumentSummaryResponse(BaseModel):
    document_id: int
    filename: str
    summary: str
    key_points: List[str]

# --- Task Execution & Tools Models ---

class TaskRequest(BaseModel):
    task_type: str = Field(..., description="calc, summarize, rewrite, datetime, todo")
    input_text: Optional[str] = ""
    parameters: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    task_type: str
    success: bool
    result: Any
    message: Optional[str] = None

class TodoItem(BaseModel):
    id: int
    task: str
    completed: bool
    created_at: str

class TodoCreate(BaseModel):
    task: str

class TodoUpdate(BaseModel):
    completed: Optional[bool] = None
    task: Optional[str] = None

# --- System & Settings Models ---

class HealthResponse(BaseModel):
    status: str
    version: str
    llm_provider: str
    available_providers: List[str]
    documents_count: int
    total_chunks: int
    conversations_count: int
    database_ok: bool

class SettingsUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    local_llm_url: Optional[str] = None
    local_llm_model: Optional[str] = None
    llm_provider: Optional[str] = None
    chunk_size: Optional[int] = None
    top_k_results: Optional[int] = None
