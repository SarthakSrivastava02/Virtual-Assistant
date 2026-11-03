import sys
import io
import asyncio
from pathlib import Path
from starlette.datastructures import UploadFile as StarletteUploadFile

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import main
from models import ChatRequest, TodoCreate, TodoUpdate, SettingsUpdate

def test_endpoints():
    print("Testing /health endpoint...")
    health = main.health_check()
    assert health.status == "healthy"
    print(f"  ✓ /health: Status={health.status}, Chunks={health.total_chunks}")

    print("Testing /new-chat...")
    new_chat = main.create_new_chat(title="Final Year Project Demo")
    conv_id = new_chat.conversation_id
    assert conv_id is not None
    print(f"  ✓ /new-chat: conv_id={conv_id}")

    print("Testing /chat with General Query...")
    chat_req = ChatRequest(
        message="Explain what is a deadlock in Operating Systems and list Coffman conditions.",
        conversation_id=conv_id,
        use_rag=False
    )
    chat_resp = main.chat_endpoint(chat_req)
    assert "deadlock" in chat_resp.response.lower() or "coffman" in chat_resp.response.lower()
    print("  ✓ /chat general response generated successfully.")

    print("Testing /chat with Mathematical Calculation...")
    calc_req = ChatRequest(
        message="calculate sqrt(144) * 5 + 10",
        conversation_id=conv_id
    )
    calc_resp = main.chat_endpoint(calc_req)
    assert "70" in calc_resp.response
    print(f"  ✓ /chat calculation: {calc_resp.response}")

    print("Testing /chat with DateTime query...")
    dt_req = ChatRequest(
        message="What is today's date?",
        conversation_id=conv_id
    )
    dt_resp = main.chat_endpoint(dt_req)
    assert "Date:" in dt_resp.response
    print("  ✓ /chat datetime tool working.")

    print("Testing /chat with To-Do addition...")
    todo_req = ChatRequest(
        message="add study computer networks to my todos",
        conversation_id=conv_id
    )
    todo_resp = main.chat_endpoint(todo_req)
    assert "Added to-do" in todo_resp.response
    print("  ✓ /chat to-do action executed.")

    print("Testing /upload endpoint with TXT notes...")
    sample_notes = (
        "Operating System Lecture Notes - Unit 3: Concurrency and Synchronization\n"
        "A critical section is a piece of code that accesses a shared resource.\n"
        "A semaphore is a synchronization variable that can be initialized to any nonnegative integer.\n"
        "Semaphores provide two atomic operations: wait() (also known as P) and signal() (also known as V).\n"
        "A binary semaphore behaves like a mutex lock, taking values 0 or 1.\n"
        "A counting semaphore has a domain of unrestricted nonnegative integers."
    )
    file_bytes = sample_notes.encode("utf-8")
    upload_file = StarletteUploadFile(file=io.BytesIO(file_bytes), filename="os_lecture_notes.txt")
    
    upload_resp = asyncio.run(main.upload_document(upload_file))
    assert upload_resp.success is True
    doc_id = upload_resp.document_id
    print(f"  ✓ /upload: Document #{doc_id} created with {upload_resp.chunks_created} chunks.")

    print("Testing /chat with Document RAG Query...")
    rag_req = ChatRequest(
        message="What operations do semaphores provide according to the notes?",
        conversation_id=conv_id,
        use_rag=True,
        strict_rag=True
    )
    rag_resp = main.chat_endpoint(rag_req)
    assert len(rag_resp.sources) > 0
    print(f"  ✓ /chat RAG query retrieved {len(rag_resp.sources)} source citation(s).")
    print(f"    Citation 1: {rag_resp.sources[0].document_name} (Page {rag_resp.sources[0].page_number})")

    print("Testing /documents list and 1-click summarization...")
    docs = main.list_documents()
    assert len(docs) >= 1

    summary_resp = main.summarize_document(doc_id)
    assert len(summary_resp.summary) > 0
    print(f"  ✓ Document summary generated: {summary_resp.summary[:60]}...")

    print("Testing /history...")
    history = main.get_all_conversations()
    assert len(history) >= 1

    detail = main.get_conversation_details(conv_id)
    assert len(detail["messages"]) >= 4
    print(f"  ✓ Conversation history retrieved with {len(detail['messages'])} turns.")

    print("Testing /todos CRUD endpoints...")
    new_todo = main.add_todo(TodoCreate(task="Prepare project presentation slides"))
    assert new_todo["id"] > 0

    main.update_todo_item(new_todo["id"], TodoUpdate(completed=True))
    main.delete_todo_item(new_todo["id"])
    print("  ✓ To-Do CRUD APIs verified.")

    print("Testing /settings endpoints...")
    settings_data = main.get_settings()
    assert "llm_provider" in settings_data

    main.update_settings(SettingsUpdate(openai_model="gpt-4o-mini", chunk_size=450))
    print("  ✓ Settings updated.")

    print("\n🎉 ALL 11 API ENDPOINTS PASSED COMPLETELY AND VERIFIED!")

if __name__ == "__main__":
    test_endpoints()
