import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from config import settings
import database
from task_executor import SafeCalculator, DateTimeTool, TextTools

SYSTEM_PROMPT_GENERAL = """You are an intelligent, articulate, and highly capable AI Virtual Assistant.
You communicate clearly, provide well-structured explanations, and format your output using clean markdown (headings, bullet points, code blocks).
When answering questions:
1. Provide accurate, direct, and well-reasoned answers matching what the user asks.
2. Be helpful, professional, polite, and articulate.
3. If code or technical information is requested, provide clear code snippets with explanations.
"""

SYSTEM_PROMPT_RAG = """You are an intelligent Knowledge Retrieval Assistant. Your role is to answer the user's question accurately using ONLY the retrieved document context below.

=== RETRIEVED CONTEXT ===
{context}
=========================

INSTRUCTIONS:
1. Prioritize the facts and definitions provided in the context above.
2. Cite the source document and page/chunk when referring to specific information.
3. If the context does not contain enough information to answer the question, clearly state:
   "Based on the uploaded documents, this information is not mentioned."
4. Do NOT hallucinate or fabricate facts not supported by the context.
"""

SYSTEM_PROMPT_STUDY_NOTES = """You are a specialized Knowledge & Study Assistant.
Your goal is to help users understand complex concepts, technical subjects, and reference documents from their uploaded files and notes.
Structure your answers with:
- 📌 **Key Definition / Concept**
- 🔍 **Detailed Explanation**
- 💡 **Key Takeaways & Formulae** (if applicable)
- 📝 **Practical Example or Summary**
"""

class LLMService:
    """
    Orchestrates LLM inference with support for:
    - Google Gemini API (Gemini Flash Lite / 3.8 Flash / Pro)
    - OpenAI API (via LangChain / official client)
    - Local LLaMA / Ollama API
    - Smart Offline Fallback Engine
    """

    def __init__(self):
        self.provider = settings.llm_provider
        self.gemini_key = settings.gemini_api_key
        self.openai_key = settings.openai_api_key
        self.langchain_llm = None
        self._init_llm()

    def _init_llm(self):
        """Initializes LangChain or direct API client if available."""
        if self.openai_key and self.openai_key.startswith("sk-"):
            try:
                from langchain_openai import ChatOpenAI
                self.langchain_llm = ChatOpenAI(
                    model=settings.openai_model,
                    temperature=settings.openai_temperature,
                    api_key=self.openai_key
                )
                print(f"[LLMService] LangChain ChatOpenAI initialized with {settings.openai_model}.")
                return
            except Exception as e:
                print(f"[LLMService] LangChain init notice: {e}.")

    def update_settings(
        self,
        gemini_key: Optional[str] = None,
        gemini_model: Optional[str] = None,
        openai_key: Optional[str] = None,
        openai_model: Optional[str] = None,
        provider: Optional[str] = None
    ):
        if gemini_key is not None:
            self.gemini_key = gemini_key.strip()
            settings.gemini_api_key = self.gemini_key
        if gemini_model is not None:
            settings.gemini_model = gemini_model.strip()
        if openai_key is not None:
            self.openai_key = openai_key.strip()
            settings.openai_api_key = self.openai_key
        if openai_model is not None:
            settings.openai_model = openai_model.strip()
        if provider is not None:
            self.provider = provider.strip()
            settings.llm_provider = self.provider
        self._init_llm()

    def generate_response(
        self,
        user_message: str,
        conversation_id: str,
        retrieved_sources: Optional[List[Dict[str, Any]]] = None,
        strict_rag: bool = False,
        mode: str = "general"
    ) -> str:
        """
        Coordinates conversation history, prompt templates, and LLM call.
        """
        # 1. Fetch recent conversation history from SQLite for conversational memory
        history = database.get_messages(conversation_id, limit=6)
        
        # 2. Build system and user prompts
        context_str = ""
        if retrieved_sources:
            context_blocks = []
            for idx, s in enumerate(retrieved_sources, start=1):
                doc_name = s.get("document_name", "Document")
                page_num = s.get("page_number", 1)
                snippet = s.get("snippet", "")
                context_blocks.append(f"[{idx}] Source: {doc_name} (Page {page_num}):\n{snippet}")
            context_str = "\n\n".join(context_blocks)

        if context_str:
            if mode == "study_notes":
                system_content = SYSTEM_PROMPT_STUDY_NOTES + "\n\n" + SYSTEM_PROMPT_RAG.format(context=context_str)
            else:
                system_content = SYSTEM_PROMPT_RAG.format(context=context_str)
        else:
            if strict_rag:
                return "⚠️ **No Relevant Documents Found:** You have 'Knowledge Assistant / Strict Notes' mode enabled, but no uploaded documents matched your query. Please upload notes/documents or disable strict mode to ask general questions."
            system_content = SYSTEM_PROMPT_GENERAL

        # 3. Determine active provider
        has_gemini = bool(self.gemini_key and len(self.gemini_key) > 8)
        has_openai = bool(self.openai_key and len(self.openai_key) > 10 and self.openai_key.startswith("sk-"))

        # Option A: Gemini API (Preferred if configured)
        if (self.provider == "gemini" or (self.provider == "auto" and has_gemini)) and has_gemini:
            try:
                reply = self._call_gemini(system_content, history, user_message)
                if reply and not reply.startswith("Error:"):
                    return reply
            except Exception as e:
                print(f"[LLMService] Gemini call error: {e}. Checking secondary providers.")

        # Option B: OpenAI API
        if (self.provider == "openai" or (self.provider == "auto" and has_openai)) and has_openai:
            try:
                return self._call_openai(system_content, history, user_message)
            except Exception as e:
                print(f"[LLMService] OpenAI call error: {e}. Falling back to Smart Engine.")

        # Option C: Local LLaMA / Ollama
        if self.provider == "local_llama" or (self.provider == "auto" and not has_gemini and not has_openai and self._check_ollama_alive()):
            try:
                return self._call_local_llama(system_content, history, user_message)
            except Exception as e:
                print(f"[LLMService] Local LLaMA call error: {e}. Falling back to Smart Engine.")

        # Option D: High-Quality Smart Engine Fallback
        return self._smart_engine_response(user_message, system_content, context_str, retrieved_sources)

    def _call_gemini(self, system_content: str, history: List[Dict[str, Any]], user_message: str) -> str:
        """
        Invokes Google Gemini API with alternating turns and appropriate timeout.
        """
        candidate_models = [
            settings.gemini_model or "gemini-flash-lite-latest",
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-flash-latest"
        ]

        # Build clean alternating contents list starting with user
        contents = []
        last_role = None

        for msg in history[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            if not contents and role != "user":
                continue
            if role == last_role:
                contents[-1]["parts"][0]["text"] += "\n\n" + msg["content"]
            else:
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
                last_role = role

        if not contents or last_role == "model":
            contents.append({"role": "user", "parts": [{"text": user_message}]})
        else:
            contents[-1]["parts"][0]["text"] += "\n\n" + user_message

        payload = {
            "system_instruction": {
                "parts": [{"text": system_content}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048
            }
        }
        json_data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        # Try candidate models with 60 second timeout for Google API processing
        last_err = None
        seen_models = set()
        for m in candidate_models:
            if m in seen_models:
                continue
            seen_models.add(m)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.gemini_key}"
            req = urllib.request.Request(url, data=json_data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                last_err = f"HTTP {e.code}: {err_body}"
                print(f"[LLMService] Gemini model '{m}' failed: {last_err}")
                continue
            except Exception as e:
                last_err = str(e)
                print(f"[LLMService] Gemini model '{m}' error: {e}")
                continue

        raise RuntimeError(f"All Gemini model candidates failed. Last error: {last_err}")

    def _call_openai(self, system_content: str, history: List[Dict[str, Any]], user_message: str) -> str:
        if self.langchain_llm is not None:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
                messages = [SystemMessage(content=system_content)]
                for msg in history[:-1]:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
                messages.append(HumanMessage(content=user_message))
                
                response = self.langchain_llm.invoke(messages)
                return response.content
            except Exception as e:
                print(f"[LLMService] LangChain invoke error: {e}, attempting direct HTTP call.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_key}"
        }

        messages = [{"role": "system", "content": system_content}]
        for msg in history[:-1]:
            if msg["role"] in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": settings.openai_model,
            "messages": messages,
            "temperature": settings.openai_temperature,
            "max_tokens": 1024
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    def _call_local_llama(self, system_content: str, history: List[Dict[str, Any]], user_message: str) -> str:
        url = f"{settings.local_llm_url.rstrip('/')}/api/chat"
        headers = {"Content-Type": "application/json"}

        messages = [{"role": "system", "content": system_content}]
        for msg in history[:-1]:
            if msg["role"] in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": settings.local_llm_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": settings.openai_temperature}
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", {}).get("content", "No response from local LLaMA.")

    def _check_ollama_alive(self) -> bool:
        try:
            url = f"{settings.local_llm_url.rstrip('/')}/api/tags"
            req = urllib.request.Request(url, headers={"User-Agent": "VirtualAssistant"}, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _smart_engine_response(
        self,
        query: str,
        system_content: str,
        context_str: str,
        sources: Optional[List[Dict[str, Any]]]
    ) -> str:
        """
        Smart fallback response generator when API connectivity is temporarily unreachable.
        """
        q_lower = query.lower().strip()

        if context_str and sources:
            snippets = [s["snippet"] for s in sources]
            doc_name = sources[0]["document_name"]
            page_num = sources[0].get("page_number", 1)
            relevance = sources[0].get("relevance_score", 0.0)

            summary = TextTools.extractive_summary("\n".join(snippets), num_sentences=4)
            
            return (
                f"### 📚 Answer from Document Context\n\n"
                f"{summary['summary']}\n\n"
                f"**Key Findings:**\n"
                + "\n".join([f"- {kp}" for kp in summary['key_points']]) + "\n\n"
                f"📌 *Primary Reference: `{doc_name}` (Page {page_num}, Confidence: {relevance:.2f})*"
            )

        knowledge_base = {
            "rag": (
                "### 🔍 Retrieval-Augmented Generation (RAG)\n\n"
                "**Retrieval-Augmented Generation (RAG)** is an AI architectural pattern that optimizes the output of a Large Language Model by referencing an authoritative external knowledge base outside its training data.\n\n"
                "**Core Pipeline:**\n"
                "1. **Document Ingestion:** Chunk documents into coherent segments (e.g., 500 characters with 100 character overlap).\n"
                "2. **Vector Embeddings:** Generate dense mathematical vectors (via SentenceTransformers or dense embeddings).\n"
                "3. **Vector Indexing:** Store vectors in a FAISS index for high-dimensional nearest neighbor search.\n"
                "4. **Semantic Retrieval:** Find top-K most similar chunks to the user's query using cosine similarity.\n"
                "5. **Augmented Prompt:** Inject retrieved chunks into the LLM system prompt for grounded, accurate generation."
            ),
            "virtual memory": (
                "### 💾 Virtual Memory in Operating Systems\n\n"
                "**Virtual Memory** is a storage allocation technique in which secondary memory can be addressed as though it were part of main memory (RAM).\n\n"
                "- **Paging:** Memory is divided into fixed-size blocks called pages (virtual) and frames (physical).\n"
                "- **Page Table:** Maps virtual addresses to physical frame addresses.\n"
                "- **Page Fault:** An interrupt that occurs when a program attempts to access data or code that is in its address space, but not currently loaded into physical RAM.\n"
                "- **Page Replacement Algorithms:** FIFO, LRU (Least Recently Used), and Optimal."
            ),
            "deadlock": (
                "### 🔒 Deadlock in Operating Systems\n\n"
                "A **deadlock** occurs in a multi-tasking system when two or more processes are unable to proceed because each is waiting for the other to release a resource.\n\n"
                "**Coffman Conditions (All 4 must hold simultaneously):**\n"
                "1. **Mutual Exclusion:** Resources cannot be shared simultaneously.\n"
                "2. **Hold and Wait:** A process holds resources while waiting for additional ones.\n"
                "3. **No Preemption:** Resources cannot be forcibly confiscated.\n"
                "4. **Circular Wait:** A closed loop of processes where each waits for a resource held by the next."
            ),
            "transformer": (
                "### 🤖 Transformer Architecture (Vaswani et al., 2017)\n\n"
                "The **Transformer** is a deep learning model architecture introduced in the paper *'Attention Is All You Need'*.\n\n"
                "- **Self-Attention Mechanism:** Allows the model to weigh the significance of different tokens in a sequence relative to each other regardless of distance.\n"
                "- **Multi-Head Attention:** Enables attending to information from different representation subspaces concurrently.\n"
                "- **Positional Encoding:** Injects sequence order information since the architecture contains no recurrence or convolutions."
            ),
            "b-tree": (
                "### 🌳 B-Trees in Database Systems\n\n"
                "A **B-Tree** is a self-balancing search tree data structure designed for disk storage systems, databases, and filesystems.\n\n"
                "- **Properties:** All leaf nodes exist at the same depth, and each internal node contains multiple keys.\n"
                "- **Time Complexity:** Search, insert, and delete operations take $\\mathcal{O}(\\log n)$ time.\n"
                "- **High Fan-Out:** Reduces disk I/O operations compared to binary search trees."
            )
        }

        for key, answer in knowledge_base.items():
            if key in q_lower:
                return answer

        if any(w in q_lower for w in ["hello", "hi", "hey", "greetings"]):
            return (
                "👋 **Hello! Welcome to your AI Virtual Assistant.**\n\n"
                "I am your conversational assistant powered by Large Language Models and Retrieval-Augmented Generation (RAG).\n\n"
                "Here is what you can do:\n"
                "- 💬 **Ask any question** on engineering, algorithms, science, or general topics.\n"
                "- 📄 **Upload documents, PDFs, or notes** to chat directly with your files (Knowledge Assistant Mode).\n"
                "- 🧮 **Perform mathematical calculations** (e.g., `calculate sqrt(144) * 25`).\n"
                "- 📝 **Manage your To-Do list** (e.g., `add review project notes to my todos`).\n"
                "- ⏰ **Check the current date and time**."
            )

        return (
            f"### 💡 Virtual Assistant Response\n\n"
            f"You asked: **\"{query}\"**\n\n"
            f"- **Knowledge Retrieval:** Upload your PDF or TXT files using the paperclip button or Knowledge Mode, and I will retrieve exact passages and answer with citations.\n"
            f"- **Task Tools:** You can execute calculations (e.g. `calculate 450 * 12`), check date/time (`what time is it?`), or manage your tasks (`add review notes to todos`)."
        )

# Global singleton
llm_service = LLMService()
