import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
FAISS_INDEX_DIR = DATA_DIR / "faiss_index"
DATABASE_PATH = DATA_DIR / "virtual_assistant.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "backend" / ".env")

class Settings(BaseModel):
    # App Information
    app_name: str = "Virtual Assistant with LLM & RAG"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    
    # Server configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Gemini API Settings
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    
    # OpenAI Settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # Local LLaMA / Ollama Settings
    local_llm_url: str = os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
    local_llm_model: str = os.getenv("LOCAL_LLM_MODEL", "llama3")
    
    # Preferred LLM Provider: 'gemini', 'openai', 'local_llama', or 'auto'
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    
    # JWT / Auth Secret
    auth_secret_key: str = os.getenv("AUTH_SECRET_KEY", "")
    
    # RAG & Embedding Settings
    embedding_model_name: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    top_k_results: int = int(os.getenv("TOP_K_RESULTS", "4"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.35"))
    
    # Upload limits
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
    allowed_extensions: list[str] = [".pdf", ".txt", ".md"]
    
    # Storage Paths
    database_path: str = str(DATABASE_PATH)
    documents_dir: str = str(DOCUMENTS_DIR)
    faiss_index_dir: str = str(FAISS_INDEX_DIR)

settings = Settings()
