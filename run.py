#!/usr/bin/env python3
"""
AI Virtual Assistant - Project Runner
Single-command launcher that initializes the database, configures the environment,
and boots the FastAPI server with the interactive React UI at http://localhost:8000.
"""

import os
import sys
import webbrowser
from pathlib import Path

# Add backend directory to path
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from config import settings
import database

def main():
    print("=" * 65)
    print(" ⚡ AI VIRTUAL ASSISTANT (LLM + RAG + ACADEMIC SUITE) ⚡")
    print("=" * 65)
    print(f" • Project Directory: {BASE_DIR}")
    print(f" • Active Provider:   {settings.llm_provider}")
    print(f" • Database:          {settings.database_path}")
    print(f" • Server Endpoint:   http://localhost:{settings.port}")
    print("=" * 65)

    # Initialize SQLite database
    print("\n[1/3] Initializing SQLite database...")
    database.init_db()

    # Check for frontend build
    frontend_dist = BASE_DIR / "frontend" / "dist" / "index.html"
    if frontend_dist.exists():
        print("[2/3] Standalone React frontend detected. Serving at root URL.")
    else:
        print("[2/3] Note: Run 'npm run build' inside frontend/ to compile Vite assets.")

    print(f"[3/3] Starting FastAPI server on http://{settings.host}:{settings.port}...")
    print("\n🚀 Application is running! Open http://localhost:8000 in your browser.")
    print("   Press CTRL+C to stop the server.\n")

    try:
        uvicorn.run("main:app", host=settings.host, port=settings.port, reload=False)
    except KeyboardInterrupt:
        print("\nServer stopped gracefully.")

if __name__ == "__main__":
    main()
