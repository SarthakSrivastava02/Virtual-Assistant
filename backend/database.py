import sqlite3
import json
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import settings

def hash_password(password: str) -> str:
    """Generates a secure SHA-256 hash with salt."""
    salt = "va_auth_salt_2026"
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def get_connection() -> sqlite3.Connection:
    """Creates and returns a SQLite connection configured for row dictionaries."""
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes SQLite tables if they do not already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # Conversations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        user_id INTEGER DEFAULT 1,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        sources TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    )
    """)

    # Documents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size_bytes INTEGER NOT NULL,
        chunk_count INTEGER NOT NULL,
        page_count INTEGER NOT NULL,
        uploaded_at TEXT NOT NULL
    )
    """)

    # Document Chunks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        content TEXT NOT NULL,
        page_number INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """)

    # To-Do Items Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    # Check and insert default demo users
    cursor.execute("SELECT id FROM users WHERE username = 'demo'")
    if not cursor.fetchone():
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, created_at) VALUES (?, ?, ?, ?)",
            ("demo", hash_password("password123"), "Demo User", now)
        )
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, created_at) VALUES (?, ?, ?, ?)",
            ("admin", hash_password("admin123"), "Administrator", now)
        )

    # Check if user_id column exists in conversations (migration check)
    try:
        cursor.execute("SELECT user_id FROM conversations LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE conversations ADD COLUMN user_id INTEGER DEFAULT 1")

    conn.commit()
    conn.close()

# Auto-initialize database on import
init_db()

# --- User & Authentication Methods ---

def create_user(username: str, password: str, full_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    clean_username = username.strip().lower()
    full_name = full_name.strip() if full_name else clean_username.capitalize()
    pwd_hash = hash_password(password)
    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, full_name, created_at) VALUES (?, ?, ?, ?)",
                (clean_username, pwd_hash, full_name, now)
            )
            user_id = cursor.lastrowid
        conn.close()
        return {"id": user_id, "username": clean_username, "full_name": full_name, "created_at": now}
    except sqlite3.IntegrityError:
        conn.close()
        return None

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    clean_username = username.strip().lower()
    pwd_hash = hash_password(password)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, created_at FROM users WHERE username = ? AND password_hash = ?", (clean_username, pwd_hash))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

# --- Conversation Methods ---

def create_conversation(title: str = "New Chat", conv_id: Optional[str] = None, user_id: int = 1) -> str:
    if not conv_id:
        conv_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO conversations (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conv_id, user_id, title, now, now)
        )
    conn.close()
    return conv_id

def get_conversations(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
            SELECT c.id, c.title, c.created_at, c.updated_at, COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.user_id = ? OR c.user_id IS NULL
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT c.id, c.title, c.created_at, c.updated_at, COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        """)
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result

def get_conversation(conv_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    conv = cursor.fetchone()
    if not conv:
        conn.close()
        return None
    conv_dict = dict(conv)
    
    cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC", (conv_id,))
    messages = []
    for row in cursor.fetchall():
        m = dict(row)
        if m["sources"]:
            try:
                m["sources"] = json.loads(m["sources"])
            except Exception:
                m["sources"] = []
        else:
            m["sources"] = []
        messages.append(m)
    conv_dict["messages"] = messages
    conn.close()
    return conv_dict

def update_conversation_title(conv_id: str, title: str):
    now = datetime.now().isoformat()
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, conv_id)
        )
    conn.close()

def update_conversation_timestamp(conv_id: str):
    now = datetime.now().isoformat()
    conn = get_connection()
    with conn:
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
    conn.close()

def delete_conversation(conv_id: str) -> bool:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def clear_all_conversations(user_id: Optional[int] = None) -> int:
    conn = get_connection()
    with conn:
        if user_id:
            cursor = conn.execute("DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = ?)", (user_id,))
            cursor = conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        else:
            conn.execute("DELETE FROM messages")
            cursor = conn.execute("DELETE FROM conversations")
    count = cursor.rowcount
    conn.close()
    return count

# --- Message Methods ---

def add_message(conv_id: str, role: str, content: str, sources: Optional[List[Dict[str, Any]]] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,))
    if not cursor.fetchone():
        create_conversation(title="Chat Session", conv_id=conv_id)
        
    now = datetime.now().isoformat()
    sources_json = json.dumps(sources) if sources else None
    with conn:
        cursor = conn.execute(
            "INSERT INTO messages (conversation_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?)",
            (conv_id, role, content, sources_json, now)
        )
        msg_id = cursor.lastrowid
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
    conn.close()
    return msg_id

def get_messages(conv_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC LIMIT ?",
        (conv_id, limit)
    )
    rows = cursor.fetchall()
    messages = []
    for r in rows:
        m = dict(r)
        if m["sources"]:
            try:
                m["sources"] = json.loads(m["sources"])
            except Exception:
                m["sources"] = []
        else:
            m["sources"] = []
        messages.append(m)
    conn.close()
    return messages

# --- Document Storage Methods ---

def add_document(filename: str, file_type: str, file_path: str, file_size: int, chunk_count: int, page_count: int) -> int:
    now = datetime.now().isoformat()
    conn = get_connection()
    with conn:
        cursor = conn.execute(
            """INSERT INTO documents (filename, file_type, file_path, file_size_bytes, chunk_count, page_count, uploaded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (filename, file_type, file_path, file_size, chunk_count, page_count, now)
        )
        doc_id = cursor.lastrowid
    conn.close()
    return doc_id

def add_document_chunks(doc_id: int, chunks: List[Dict[str, Any]]):
    conn = get_connection()
    with conn:
        for c in chunks:
            conn.execute(
                "INSERT INTO document_chunks (document_id, chunk_index, content, page_number) VALUES (?, ?, ?, ?)",
                (doc_id, c.get("chunk_index", 0), c.get("text", ""), c.get("page_number", 1))
            )
    conn.close()

def get_documents() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_document(doc_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_document_chunks(doc_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM document_chunks WHERE document_id = ? ORDER BY chunk_index ASC",
        (doc_id,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_chunks() -> List[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT dc.id, dc.document_id, dc.chunk_index, dc.content, dc.page_number, d.filename
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            ORDER BY dc.document_id, dc.chunk_index
        """)
        rows = [dict(r) for r in cursor.fetchall()]
    except Exception:
        rows = []
    finally:
        conn.close()
    return rows

def delete_document(doc_id: int) -> bool:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (doc_id,))
        cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# --- To-Do Item Methods ---

def add_todo(task: str) -> int:
    now = datetime.now().isoformat()
    conn = get_connection()
    with conn:
        cursor = conn.execute("INSERT INTO todos (task, completed, created_at) VALUES (?, 0, ?)", (task, now))
        todo_id = cursor.lastrowid
    conn.close()
    return todo_id

def get_todos() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, task, completed, created_at FROM todos ORDER BY id DESC")
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        d["completed"] = bool(d["completed"])
        rows.append(d)
    conn.close()
    return rows

def update_todo(todo_id: int, completed: Optional[bool] = None, task: Optional[str] = None) -> bool:
    conn = get_connection()
    with conn:
        if completed is not None and task is not None:
            cursor = conn.execute("UPDATE todos SET completed = ?, task = ? WHERE id = ?", (1 if completed else 0, task, todo_id))
        elif completed is not None:
            cursor = conn.execute("UPDATE todos SET completed = ? WHERE id = ?", (1 if completed else 0, todo_id))
        elif task is not None:
            cursor = conn.execute("UPDATE todos SET task = ? WHERE id = ?", (task, todo_id))
        else:
            conn.close()
            return False
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def delete_todo(todo_id: int) -> bool:
    conn = get_connection()
    with conn:
        cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
