import os
import json
import hashlib
from typing import List, Dict, Tuple
import numpy as np
from PyPDF2 import PdfReader
import docx
from pathlib import Path


INDEX_DIR = ".rag_index"
INDEX_FILE = os.path.join(INDEX_DIR, "index.npz")
META_FILE = os.path.join(INDEX_DIR, "meta.json")
SUBJECT_INDEX_FILE = os.path.join(INDEX_DIR, "subjects.json")


def _ensure_index_dir() -> None:
    if not os.path.isdir(INDEX_DIR):
        os.makedirs(INDEX_DIR, exist_ok=True)


def _chunk_text(text: str, max_tokens: int = 450, overlap: int = 60) -> List[str]:
    """Chunk text with better subject-aware splitting"""
    words = text.split()
    if not words:
        return []
    
    chunks = []
    start = 0
    step = max(1, max_tokens - overlap)
    
    while start < len(words):
        end = min(len(words), start + max_tokens)
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += step
    
    return chunks


def _extract_subject_from_filename(filename: str) -> str:
    """Extract subject from filename"""
    filename_lower = filename.lower()
    
    # Common subject keywords
    subjects = {
        'mathematics': ['math', 'calculus', 'algebra', 'statistics', 'geometry'],
        'physics': ['physics', 'mechanics', 'thermodynamics', 'quantum'],
        'chemistry': ['chemistry', 'organic', 'inorganic', 'biochemistry'],
        'biology': ['biology', 'anatomy', 'physiology', 'genetics'],
        'computer_science': ['computer', 'programming', 'algorithm', 'software'],
        'business': ['business', 'finance', 'economics', 'management', 'marketing'],
        'history': ['history', 'historical', 'ancient', 'medieval'],
        'literature': ['literature', 'english', 'poetry', 'novel'],
        'psychology': ['psychology', 'psychiatric', 'behavioral'],
        'engineering': ['engineering', 'mechanical', 'electrical', 'civil']
    }
    
    for subject, keywords in subjects.items():
        if any(keyword in filename_lower for keyword in keywords):
            return subject
    
    return 'general'


def _read_pdf_to_chunks(pdf_path: str) -> List[Tuple[str, int, str, str]]:
    """Read PDF and return chunks with subject information"""
    reader = PdfReader(pdf_path)
    results: List[Tuple[str, int, str, str]] = []
    subject = _extract_subject_from_filename(os.path.basename(pdf_path))
    
    for page_idx, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        
        for chunk in _chunk_text(text):
            if chunk.strip():
                results.append((os.path.basename(pdf_path), page_idx, chunk, subject))
    
    return results


def _read_docx_to_chunks(docx_path: str) -> List[Tuple[str, int, str, str]]:
    """Read DOCX and return chunks with subject information"""
    try:
        doc = docx.Document(docx_path)
        results: List[Tuple[str, int, str, str]] = []
        subject = _extract_subject_from_filename(os.path.basename(docx_path))
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        for chunk in _chunk_text(text):
            if chunk.strip():
                results.append((os.path.basename(docx_path), 1, chunk, subject))
        
        return results
    except Exception as e:
        print(f"Error reading DOCX {docx_path}: {e}")
        return []


def _read_txt_to_chunks(txt_path: str) -> List[Tuple[str, int, str, str]]:
    """Read TXT and return chunks with subject information"""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        results: List[Tuple[str, int, str, str]] = []
        subject = _extract_subject_from_filename(os.path.basename(txt_path))
        
        for chunk in _chunk_text(text):
            if chunk.strip():
                results.append((os.path.basename(txt_path), 1, chunk, subject))
        
        return results
    except Exception as e:
        print(f"Error reading TXT {txt_path}: {e}")
        return []


def _simple_embed(text: str) -> np.ndarray:
    """Simple TF-IDF style embedding using word hashing"""
    words = text.lower().split()
    embedding = np.zeros(128)
    
    for word in words:
        word_hash = hash(word) % 128
        embedding[word_hash] += 1
    
    # Normalize
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding.astype(np.float32)


def _embed_texts(texts: List[str]) -> np.ndarray:
    """Use simple hash-based embeddings"""
    embeddings = []
    for text in texts:
        embeddings.append(_simple_embed(text))
    return np.vstack(embeddings)


def build_index(api_key: str, pdf_dir: str = "pdf", upload_dir: str = "uploads") -> Dict[str, int]:
    """Build RAG index from both pdf and uploads directories"""
    _ensure_index_dir()
    all_chunks: List[Tuple[str, int, str, str]] = []
    subjects = set()
    
    # Process PDF directory
    if os.path.exists(pdf_dir):
        for name in os.listdir(pdf_dir):
            if name.lower().endswith(".pdf"):
                path = os.path.join(pdf_dir, name)
                chunks = _read_pdf_to_chunks(path)
                all_chunks.extend(chunks)
                subjects.update([chunk[3] for chunk in chunks])
    
    # Process uploads directory
    if os.path.exists(upload_dir):
        for name in os.listdir(upload_dir):
            path = os.path.join(upload_dir, name)
            if name.lower().endswith(".pdf"):
                chunks = _read_pdf_to_chunks(path)
                all_chunks.extend(chunks)
                subjects.update([chunk[3] for chunk in chunks])
            elif name.lower().endswith((".docx", ".doc")):
                chunks = _read_docx_to_chunks(path)
                all_chunks.extend(chunks)
                subjects.update([chunk[3] for chunk in chunks])
            elif name.lower().endswith(".txt"):
                chunks = _read_txt_to_chunks(path)
                all_chunks.extend(chunks)
                subjects.update([chunk[3] for chunk in chunks])
    
    if not all_chunks:
        raise RuntimeError("No content found to index.")
    
    texts = [t for (_, _, t, _) in all_chunks]
    embeddings = _embed_texts(texts)
    
    # Save index
    np.savez_compressed(INDEX_FILE, embeddings=embeddings)
    
    # Save metadata with subject information
    meta = [{"file": f, "page": p, "text": t, "subject": s} for (f, p, t, s) in all_chunks]
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    
    # Save subject index
    subject_stats = {}
    for subject in subjects:
        subject_chunks = [m for m in meta if m["subject"] == subject]
        subject_stats[subject] = {
            "chunks": len(subject_chunks),
            "files": len(set(m["file"] for m in subject_chunks))
        }
    
    with open(SUBJECT_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(subject_stats, f, ensure_ascii=False)
    
    return {
        "chunks": len(meta),
        "dim": int(embeddings.shape[1]) if embeddings.size else 0,
        "subjects": list(subjects),
        "subject_stats": subject_stats
    }


def _load_index() -> Tuple[np.ndarray, List[Dict[str, str]]]:
    """Load the RAG index"""
    if not (os.path.isfile(INDEX_FILE) and os.path.isfile(META_FILE)):
        raise RuntimeError("RAG index not built. Please build the index first.")
    
    data = np.load(INDEX_FILE)
    embeddings: np.ndarray = data["embeddings"]
    
    with open(META_FILE, "r", encoding="utf-8") as f:
        meta: List[Dict[str, str]] = json.load(f)
    
    return embeddings, meta


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity"""
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return np.dot(a_norm, b_norm.T)


def retrieve(api_key: str, query: str, k: int = 5, subject_filter: str = None) -> List[Dict[str, str]]:
    """Retrieve similar chunks with optional subject filtering"""
    embeddings, meta = _load_index()
    
    # Filter by subject if specified
    if subject_filter and subject_filter != "all":
        meta = [m for m in meta if m.get("subject", "general") == subject_filter]
        if not meta:
            return []
        
        # Get indices of filtered chunks
        filtered_indices = [i for i, m in enumerate(meta) if m.get("subject", "general") == subject_filter]
        embeddings = embeddings[filtered_indices]
    
    q_vec = _embed_texts([query])
    sims = _cosine_sim(q_vec, embeddings)[0]
    top_idx = np.argsort(-sims)[:k]
    
    results = []
    for idx in top_idx:
        m = meta[int(idx)].copy()
        m["score"] = float(sims[int(idx)])
        results.append(m)
    
    return results


def get_available_subjects() -> List[str]:
    """Get list of available subjects in the index"""
    if not os.path.isfile(SUBJECT_INDEX_FILE):
        return []
    
    with open(SUBJECT_INDEX_FILE, "r", encoding="utf-8") as f:
        subject_stats = json.load(f)
    
    return list(subject_stats.keys())


def get_subject_stats() -> Dict[str, Dict[str, int]]:
    """Get statistics about subjects in the index"""
    if not os.path.isfile(SUBJECT_INDEX_FILE):
        return {}
    
    with open(SUBJECT_INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
