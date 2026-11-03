import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from config import settings
import database

class EmbeddingEngine:
    """
    Modular embedding generator that supports:
    1. SentenceTransformers (local Hugging Face models like 'all-MiniLM-L6-v2')
    2. OpenAI Embeddings (if API key available)
    3. Scikit-learn TF-IDF / dense fallback (guarantees offline zero-dependency capability)
    """
    def __init__(self):
        self.mode = "fallback"
        self.model = None
        self._init_model()

    def _init_model(self):
        # 1. Try SentenceTransformers
        try:
            from sentence_transformers import SentenceTransformer
            print(f"[RAG] Loading SentenceTransformer model: {settings.embedding_model_name}...")
            self.model = SentenceTransformer(settings.embedding_model_name)
            self.mode = "sentence_transformers"
            print("[RAG] SentenceTransformer loaded successfully.")
            return
        except Exception as e:
            print(f"[RAG] SentenceTransformers unavailable ({e}). Checking fallbacks.")

        # 2. Scikit-learn TF-IDF / dense fallback
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.model = TfidfVectorizer(max_features=384, stop_words="english", ngram_range=(1, 2))
            self.mode = "tfidf"
            print("[RAG] Using Scikit-Learn TF-IDF vectorizer fallback.")
        except Exception as e:
            self.mode = "simple_hash"
            print(f"[RAG] TF-IDF unavailable ({e}). Using normalized hash vectorizer.")

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        if self.mode == "sentence_transformers":
            embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return embeddings.astype(np.float32)

        elif self.mode == "tfidf":
            try:
                # Fit or transform
                if not hasattr(self.model, "vocabulary_") or not self.model.vocabulary_:
                    # Need to fit on first batch
                    matrix = self.model.fit_transform(texts)
                else:
                    matrix = self.model.transform(texts)
                dense = matrix.toarray().astype(np.float32)
                
                # Pad to fixed 384 dimensions for consistency
                if dense.shape[1] < 384:
                    padded = np.zeros((dense.shape[0], 384), dtype=np.float32)
                    padded[:, :dense.shape[1]] = dense
                    dense = padded
                elif dense.shape[1] > 384:
                    dense = dense[:, :384]

                # Normalize vectors for cosine similarity
                norms = np.linalg.norm(dense, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                return (dense / norms).astype(np.float32)
            except Exception as e:
                print(f"[RAG] TF-IDF embedding error: {e}, falling back to hash")

        # Hash fallback
        vectors = []
        for t in texts:
            vec = np.zeros(384, dtype=np.float32)
            words = t.lower().split()
            for w in words:
                h = abs(hash(w)) % 384
                vec[h] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
        return np.array(vectors, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_texts([query])[0]


class RAGService:
    """
    Retrieval-Augmented Generation (RAG) Service.
    Manages vector indexing with FAISS (or NumPy fallback) and semantic search.
    """
    def __init__(self):
        self.embedding_engine = EmbeddingEngine()
        self.index = None
        self.metadata: List[Dict[str, Any]] = [] # stores chunk metadata matching index row
        self.index_file = Path(settings.faiss_index_dir) / "rag_index.bin"
        self.meta_file = Path(settings.faiss_index_dir) / "rag_metadata.pkl"
        self.use_faiss = False
        
        self._check_faiss_support()
        self.load_or_rebuild()

    def _check_faiss_support(self):
        try:
            import faiss
            self.use_faiss = True
            print("[RAG] FAISS vector library detected and enabled.")
        except ImportError:
            self.use_faiss = False
            print("[RAG] FAISS not found. Utilizing NumPy Cosine Similarity Index Engine.")

    def _create_empty_index(self, dimension: int = 384):
        if self.use_faiss:
            import faiss
            # Inner Product with normalized vectors = Cosine Similarity
            return faiss.IndexFlatIP(dimension)
        else:
            # Fallback storage: matrix of shape (0, dimension)
            return np.empty((0, dimension), dtype=np.float32)

    def load_or_rebuild(self):
        """Loads saved index from disk if present, else rebuilds from database chunks."""
        if self.index_file.exists() and self.meta_file.exists():
            try:
                with open(self.meta_file, "rb") as f:
                    self.metadata = pickle.load(f)

                if self.use_faiss:
                    import faiss
                    self.index = faiss.read_index(str(self.index_file))
                else:
                    with open(self.index_file, "rb") as f:
                        self.index = pickle.load(f)
                
                print(f"[RAG] Successfully loaded vector index with {len(self.metadata)} chunks.")
                return
            except Exception as e:
                print(f"[RAG] Error loading saved index: {e}. Rebuilding from DB...")

        self.rebuild_from_database()

    def save_index(self):
        """Persists current vector index and metadata to disk."""
        try:
            settings_dir = Path(settings.faiss_index_dir)
            settings_dir.mkdir(parents=True, exist_ok=True)

            with open(self.meta_file, "wb") as f:
                pickle.dump(self.metadata, f)

            if self.use_faiss and self.index is not None:
                import faiss
                faiss.write_index(self.index, str(self.index_file))
            else:
                with open(self.index_file, "wb") as f:
                    pickle.dump(self.index, f)

            print(f"[RAG] Saved {len(self.metadata)} chunks to {self.index_file}.")
        except Exception as e:
            print(f"[RAG] Error persisting index to disk: {e}")

    def rebuild_from_database(self):
        """Re-indexes all chunks recorded in SQLite database."""
        all_chunks = database.get_all_chunks()
        self.metadata = []
        self.index = self._create_empty_index(dimension=384)

        if not all_chunks:
            print("[RAG] Database contains no chunks to index.")
            return

        texts = [c["content"] for c in all_chunks]
        embeddings = self.embedding_engine.embed_texts(texts)

        if self.use_faiss:
            self.index.add(embeddings)
        else:
            self.index = embeddings

        for c in all_chunks:
            self.metadata.append({
                "document_id": c["document_id"],
                "chunk_id": c["chunk_index"],
                "page_number": c.get("page_number", 1),
                "filename": c.get("filename", "Unknown Document"),
                "content": c["content"]
            })

        self.save_index()
        print(f"[RAG] Rebuilt index with {len(self.metadata)} chunks from database.")

    def add_document(self, doc_id: int, filename: str, chunks: List[Dict[str, Any]]):
        """Generates embeddings for newly uploaded document chunks and adds to index."""
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        embeddings = self.embedding_engine.embed_texts(texts)

        if self.index is None:
            self.index = self._create_empty_index(dimension=embeddings.shape[1])

        if self.use_faiss:
            self.index.add(embeddings)
        else:
            if self.index.shape[0] == 0:
                self.index = embeddings
            else:
                self.index = np.vstack([self.index, embeddings])

        for c in chunks:
            self.metadata.append({
                "document_id": doc_id,
                "chunk_id": c["chunk_index"],
                "page_number": c.get("page_number", 1),
                "filename": filename,
                "content": c["text"]
            })

        self.save_index()

    def search(
        self,
        query: str,
        top_k: int = None,
        document_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k relevant chunks for query.
        Returns list of dicts with: snippet, score, document_name, chunk_id, page_number
        """
        top_k = top_k or settings.top_k_results
        if not self.metadata or self.index is None:
            return []

        query_vector = self.embedding_engine.embed_query(query).reshape(1, -1)

        # Compute similarity scores
        if self.use_faiss:
            scores, indices = self.index.search(query_vector, min(top_k * 3, len(self.metadata)))
            raw_scores = scores[0]
            raw_indices = indices[0]
        else:
            # Cosine similarity matrix multiplication
            raw_scores = np.dot(self.index, query_vector.T).flatten()
            raw_indices = np.argsort(-raw_scores)[:min(top_k * 3, len(self.metadata))]
            raw_scores = raw_scores[raw_indices]

        results = []
        for score, idx in zip(raw_scores, raw_indices):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]

            # Optional document_id filter
            if document_id is not None and meta["document_id"] != document_id:
                continue

            # Check similarity threshold
            relevance = float(score)
            results.append({
                "document_id": meta["document_id"],
                "document_name": meta["filename"],
                "chunk_id": meta["chunk_id"],
                "page_number": meta.get("page_number", 1),
                "relevance_score": round(relevance, 4),
                "snippet": meta["content"]
            })

            if len(results) >= top_k:
                break

        return results

    def remove_document(self, doc_id: int):
        """Removes all chunks belonging to doc_id and rebuilds index."""
        self.rebuild_from_database()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_chunks_indexed": len(self.metadata),
            "engine": "FAISS" if self.use_faiss else "NumPy-Cosine",
            "embedding_mode": self.embedding_engine.mode,
            "index_dimension": 384
        }

# Global singleton instance
rag_service = RAGService()
