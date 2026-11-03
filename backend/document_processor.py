import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from config import settings

class DocumentProcessor:
    """
    Handles file validation, text extraction from PDF and TXT/MD files,
    and intelligent text chunking with overlap for RAG ingestion.
    """

    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in settings.allowed_extensions

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        # Keep only alphanumeric, dashes, dots, and underscores
        clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
        return clean_name or "uploaded_document.txt"

    @classmethod
    def extract_text_from_file(cls, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts full text and page-by-page content.
        Returns: (full_text, pages_list)
        where pages_list contains dicts: [{"page_number": int, "text": str}]
        """
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return cls._extract_from_pdf(file_path)
        elif ext in [".txt", ".md", ".csv", ".json"]:
            return cls._extract_from_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @classmethod
    def _extract_from_pdf(cls, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        pages = []
        full_text_parts = []
        
        # 1. Attempt pypdf first if available
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for idx, page in enumerate(reader.pages):
                extracted = page.extract_text() or ""
                cleaned = cls._clean_text(extracted)
                if cleaned:
                    pages.append({"page_number": idx + 1, "text": cleaned})
                    full_text_parts.append(cleaned)
            if full_text_parts:
                return "\n\n".join(full_text_parts), pages
        except ImportError:
            pass
        except Exception as e:
            print(f"[DocumentProcessor] pypdf extraction warning: {e}. Falling back to stream parser.")

        # 2. Pure-Python fallback parser for PDF text streams
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            # Simple PDF page splitter & text stream extractor
            page_chunks = content.split(b"/Page\n")
            if len(page_chunks) <= 1:
                page_chunks = content.split(b"/Type /Page")

            for page_num, raw_chunk in enumerate(page_chunks[1:], start=1):
                # Search for strings inside parentheses (Tj operator) or text blocks
                matches = re.findall(rb'\((.*?)\)\s*T[jJ]', raw_chunk)
                extracted_lines = []
                for m in matches:
                    try:
                        text_part = m.decode("latin1", errors="ignore")
                        if text_part.strip():
                            extracted_lines.append(text_part)
                    except Exception:
                        pass
                
                # Also try stream extraction if available
                if not extracted_lines:
                    streams = re.findall(rb'stream[\r\n]+(.*?)[\r\n]+endstream', raw_chunk, re.DOTALL)
                    for stream in streams:
                        try:
                            import zlib
                            decompressed = zlib.decompress(stream)
                            stream_matches = re.findall(rb'\((.*?)\)\s*T[jJ]', decompressed)
                            for sm in stream_matches:
                                line = sm.decode("latin1", errors="ignore")
                                if line.strip():
                                    extracted_lines.append(line)
                        except Exception:
                            continue

                page_text = " ".join(extracted_lines).strip()
                if page_text:
                    cleaned = cls._clean_text(page_text)
                    pages.append({"page_number": page_num, "text": cleaned})
                    full_text_parts.append(cleaned)

            if full_text_parts:
                return "\n\n".join(full_text_parts), pages
        except Exception as e:
            print(f"[DocumentProcessor] Stream parser fallback error: {e}")

        # If empty or unparseable, provide minimal notification
        if not full_text_parts:
            return "No extractable text found in PDF.", [{"page_number": 1, "text": "No text extracted."}]

        return "\n\n".join(full_text_parts), pages

    @classmethod
    def _extract_from_text_file(cls, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        encodings = ["utf-8", "latin-1", "cp1252"]
        content = ""
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        cleaned = cls._clean_text(content)
        pages = [{"page_number": 1, "text": cleaned}]
        return cleaned, pages

    @classmethod
    def _clean_text(cls, text: str) -> str:
        if not text:
            return ""
        # Normalize whitespace while preserving paragraphs
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @classmethod
    def chunk_document(
        cls,
        pages: List[Dict[str, Any]],
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Splits pages into smaller semantically coherent chunks with overlap.
        Preserves page number and metadata for RAG citations.
        """
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        chunks = []
        global_chunk_idx = 0

        for page in pages:
            page_num = page.get("page_number", 1)
            text = page.get("text", "")
            if not text:
                continue

            # Recursive character splitting strategy
            page_chunks = cls._split_text_with_overlap(text, chunk_size, chunk_overlap)
            for ch in page_chunks:
                if len(ch.strip()) > 20: # ignore trivial noise
                    chunks.append({
                        "chunk_index": global_chunk_idx,
                        "text": ch.strip(),
                        "page_number": page_num
                    })
                    global_chunk_idx += 1

        return chunks

    @classmethod
    def _split_text_with_overlap(cls, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            if end >= text_len:
                chunks.append(text[start:text_len])
                break

            # Find best natural break point (paragraph > sentence > word > hard break)
            candidate = text[start:end]
            break_point = -1

            # Check for double newline (paragraph boundary)
            p_break = candidate.rfind("\n\n")
            if p_break > chunk_size // 2:
                break_point = start + p_break + 2
            else:
                # Check for sentence boundary (". ", "? ", "! ", "\n")
                s_break = max(
                    candidate.rfind(". "),
                    candidate.rfind(".\n"),
                    candidate.rfind("? "),
                    candidate.rfind("! "),
                    candidate.rfind("\n")
                )
                if s_break > chunk_size // 3:
                    break_point = start + s_break + 1
                else:
                    # Check for space (word boundary)
                    w_break = candidate.rfind(" ")
                    if w_break > chunk_size // 3:
                        break_point = start + w_break + 1
                    else:
                        break_point = end

            chunk_str = text[start:break_point].strip()
            if chunk_str:
                chunks.append(chunk_str)

            # Shift start by overlap
            start = max(start + 1, break_point - chunk_overlap)

        return chunks
