"""
Simple RAG Pipeline package.
Step 1: Read text from input PDF (PDFReader)
Step 2: Convert text into chunks (TextChunker)
Step 3: Embed using all-MiniLM-L6-v2 & store in ChromaDB (ChromaVectorStore)
Step 4: User query interface (CLI & Streamlit)
Step 5: Query embedding & top-k retrieval (ChromaVectorStore)
Step 6: Contextual generation using modular LLM generator (ModularGenerator)
"""

try:
    from src.rag_pipeline.config import RAGConfig
    from src.rag_pipeline.pdf_reader import PDFReader, extract_text_from_pdf
    from src.rag_pipeline.chunker import TextChunker, chunk_text
    from src.rag_pipeline.vector_store import ChromaVectorStore
    from src.rag_pipeline.generator import ModularGenerator
    from src.rag_pipeline.pipeline import RAGPipeline
    from src.rag_pipeline.voice import clean_text_for_speech, text_to_speech_base64
except ImportError:
    from .config import RAGConfig
    from .pdf_reader import PDFReader, extract_text_from_pdf
    from .chunker import TextChunker, chunk_text
    from .vector_store import ChromaVectorStore
    from .generator import ModularGenerator
    from .pipeline import RAGPipeline
    from .voice import clean_text_for_speech, text_to_speech_base64

__all__ = [
    "RAGConfig",
    "PDFReader",
    "extract_text_from_pdf",
    "TextChunker",
    "chunk_text",
    "ChromaVectorStore",
    "ModularGenerator",
    "RAGPipeline",
    "clean_text_for_speech",
    "text_to_speech_base64"
]
