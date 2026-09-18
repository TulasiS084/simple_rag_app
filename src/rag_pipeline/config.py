from dataclasses import dataclass, field
from typing import Optional
import os

@dataclass
class RAGConfig:
    """Configuration settings for the RAG pipeline."""
    chunk_size: int = 1000
    chunk_overlap: int = 150
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_db_dir: Optional[str] = os.path.join(os.getcwd(), "chroma_db")
    collection_name: str = "rag_collection"
    top_k: int = 4
    llm_provider: str = "fallback"  # "fallback", "huggingface", "gemini", "openai"
    model_name: Optional[str] = None
    temperature: float = 0.2
    max_new_tokens: int = 256
