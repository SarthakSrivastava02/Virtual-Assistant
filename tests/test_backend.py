import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import database
from document_processor import DocumentProcessor
from task_executor import SafeCalculator, DateTimeTool, TextTools, IntentDetector, task_executor
from rag_service import rag_service
from llm_service import llm_service

def test_database():
    print("Testing database initialization...")
    database.init_db()
    
    # Test conversation creation
    conv_id = database.create_conversation("Unit Test Chat")
    assert conv_id is not None
    print(f"Created conversation: {conv_id}")

    # Test message insertion
    msg_id = database.add_message(conv_id, "user", "What is virtual memory?")
    assert msg_id > 0
    print(f"Added message #{msg_id}")

    messages = database.get_messages(conv_id)
    assert len(messages) == 1
    assert messages[0]["content"] == "What is virtual memory?"

    # Test todo CRUD
    todo_id = database.add_todo("Complete Final Year Project")
    todos = database.get_todos()
    assert any(t["id"] == todo_id for t in todos)
    print(f"Added todo #{todo_id}")

    database.update_todo(todo_id, completed=True)
    todos = database.get_todos()
    for t in todos:
        if t["id"] == todo_id:
            assert t["completed"] is True
    print("Database tests passed!")

def test_calculator():
    print("Testing Safe AST Calculator...")
    cases = [
        ("25 + 75", 100),
        ("12 * 12", 144),
        ("sqrt(144) + 10", 22),
        ("(5 + 3) * 2^3", 64),
        ("100 / 4", 25),
        ("abs(-42)", 42),
    ]
    for expr, expected in cases:
        ok, res, msg = SafeCalculator.evaluate(expr)
        assert ok, f"Failed on {expr}: {msg}"
        assert abs(res - expected) < 1e-4, f"Mismatch for {expr}: expected {expected}, got {res}"
        print(f"  ✓ {expr} = {res}")

    # Test safety: arbitrary expressions must be rejected
    bad_expr = "__import__('os').system('ls')"
    ok, res, msg = SafeCalculator.evaluate(bad_expr)
    assert not ok, "Security failure: malicious expression was not rejected!"
    print("  ✓ Malicious code injection properly blocked!")

def test_datetime_and_tools():
    print("Testing DateTime & Text Tools...")
    dt_info = DateTimeTool.get_info()
    assert "date" in dt_info
    print(f"  ✓ Date/Time: {dt_info['date']} at {dt_info['current_time_12h']}")

    text = (
        "Operating systems provide memory management, process scheduling, and file systems. "
        "Virtual memory allows execution of processes that may not be completely in memory. "
        "Paging avoids external fragmentation and need for compaction. "
        "Demand paging brings pages into memory only when needed during execution."
    )
    summary = TextTools.extractive_summary(text, num_sentences=2)
    assert len(summary["key_points"]) <= 2
    print(f"  ✓ Extractive Summary: {summary['summary'][:60]}...")

def test_intent_detection():
    print("Testing Intent Detector...")
    assert IntentDetector.detect_intent("calculate 15 * 30") == "calculation"
    assert IntentDetector.detect_intent("what time is it?") == "datetime"
    assert IntentDetector.detect_intent("add revise calculus to my todos") == "todo"
    assert IntentDetector.detect_intent("what is a deadlock in OS?") == "general"
    print("  ✓ Intent classification successful!")

def test_rag_and_document_processor():
    print("Testing Document Processor and RAG Index...")
    sample_text = (
        "Artificial Intelligence is a field of computer science dedicated to building systems capable of "
        "performing tasks that typically require human intelligence. Machine learning is a subset of AI "
        "that focuses on the development of algorithms that learn from data to improve their performance over time. "
        "Deep learning uses neural networks with many layers to model complex representations. "
        "Natural Language Processing (NLP) enables computers to understand, interpret, and generate human language."
    )
    pages = [{"page_number": 1, "text": sample_text}]
    chunks = DocumentProcessor.chunk_document(pages, chunk_size=150, chunk_overlap=30)
    assert len(chunks) >= 2
    print(f"  ✓ Generated {len(chunks)} chunks with overlap.")

    # Add document to database and RAG
    doc_id = database.add_document("sample_ai_notes.txt", ".txt", "/tmp/fake.txt", len(sample_text), len(chunks), 1)
    database.add_document_chunks(doc_id, chunks)
    rag_service.add_document(doc_id, "sample_ai_notes.txt", chunks)

    # Search for machine learning
    results = rag_service.search("What is machine learning?", top_k=2)
    assert len(results) > 0
    print(f"  ✓ RAG Search returned {len(results)} hit(s). Top hit score: {results[0]['relevance_score']}")

    # Clean up test doc
    database.delete_document(doc_id)
    rag_service.remove_document(doc_id)
    print("  ✓ RAG and Document processing tests passed!")

if __name__ == "__main__":
    test_database()
    test_calculator()
    test_datetime_and_tools()
    test_intent_detection()
    test_rag_and_document_processor()
    print("\n🎉 ALL BACKEND COMPONENT TESTS PASSED!")
