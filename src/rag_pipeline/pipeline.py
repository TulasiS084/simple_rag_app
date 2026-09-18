import os
import logging
from typing import Optional, Dict, Any, List

try:
    from src.rag_pipeline.config import RAGConfig
    from src.rag_pipeline.pdf_reader import PDFReader, DocumentReader, extract_text_from_pdf, extract_text_from_document
    from src.rag_pipeline.chunker import TextChunker, chunk_text
    from src.rag_pipeline.vector_store import ChromaVectorStore
    from src.rag_pipeline.generator import ModularGenerator
except ImportError:
    from rag_pipeline.config import RAGConfig
    from rag_pipeline.pdf_reader import PDFReader, DocumentReader, extract_text_from_pdf, extract_text_from_document
    from rag_pipeline.chunker import TextChunker, chunk_text
    from rag_pipeline.vector_store import ChromaVectorStore
    from rag_pipeline.generator import ModularGenerator

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    End-to-end RAG Pipeline orchestrating:
    Step 1: Reading text from input PDF or any document format
    Step 2: Converting text into chunks
    Step 3: Embedding input using all-MiniLM-L6-v2 & storing in ChromaDB
    Step 4: Providing interface for user query
    Step 5: Embedding query & extracting top-k chunks from ChromaDB
    Step 6: Generating response considering retrieved chunks as context
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.vector_store = ChromaVectorStore(
            persist_directory=self.config.chroma_db_dir,
            collection_name=self.config.collection_name,
            embedding_model_name=self.config.embedding_model
        )
        self.generator = ModularGenerator(
            default_provider=self.config.llm_provider,
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            max_new_tokens=self.config.max_new_tokens
        )
        self.document_reader = DocumentReader()
        self.indexed_files: List[Dict[str, Any]] = []

    def ingest(
        self,
        file_path: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Step 1, Step 2, and Step 3:
        Reads document (PDF, TXT, MD, DOCX), chunks text, embeds and stores in ChromaDB.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found at: {file_path}")

        filename = os.path.basename(file_path)

        # Step 1: Read text from input document
        logger.info(f"Step 1: Reading document from {file_path}")
        sections = extract_text_from_document(file_path)
        if not sections:
            raise ValueError(f"No extractable text found in file: {filename}")

        # Step 2: Convert extracted text into chunks
        c_size = chunk_size or self.config.chunk_size
        c_overlap = chunk_overlap or self.config.chunk_overlap
        logger.info(f"Step 2: Chunking text (size={c_size}, overlap={c_overlap})")

        all_chunks: List[Dict[str, Any]] = []
        for section in sections:
            sec_text = section["text"]
            sec_meta = section["metadata"]
            chunks = chunk_text(
                text=sec_text,
                chunk_size=c_size,
                chunk_overlap=c_overlap,
                metadata=sec_meta
            )
            all_chunks.extend(chunks)

        # Step 3: Embed using sentence-transformers and store in ChromaDB
        logger.info(f"Step 3: Storing {len(all_chunks)} chunks in ChromaDB with embeddings")
        self.vector_store.add_chunks(all_chunks)

        file_stat = {
            "filename": filename,
            "path": file_path,
            "sections_processed": len(sections),
            "chunks_processed": len(all_chunks),
            "file_type": os.path.splitext(filename)[1].lower()
        }
        self.indexed_files.append(file_stat)

        return {
            "status": "success",
            "file_path": file_path,
            "filename": filename,
            "pages_processed": len(sections),
            "chunks_processed": len(all_chunks)
        }

    def ingest_multiple(
        self,
        file_paths: List[str],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Dict[str, Any]:
        """Batch ingest multiple document files."""
        total_chunks = 0
        successful_files = []
        errors = []

        for path in file_paths:
            try:
                res = self.ingest(path, chunk_size, chunk_overlap)
                total_chunks += res.get("chunks_processed", 0)
                successful_files.append(os.path.basename(path))
            except Exception as e:
                errors.append({"file": os.path.basename(path), "error": str(e)})

        return {
            "status": "success" if not errors else ("partial" if successful_files else "failed"),
            "files_processed": successful_files,
            "total_chunks": total_chunks,
            "errors": errors
        }

    def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        model_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 5 & Step 6:
        Embeds the query, extracts top-k chunks from vector DB,
        and generates a response considering the chunks as context.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        k = top_k or self.config.top_k

        # Step 5: Embed query and extract top-k chunks from ChromaDB
        logger.info(f"Step 5: Retrieving top {k} chunks for query: '{query}'")
        retrieved_chunks = self.vector_store.query(query_text=query, top_k=k)

        # Step 6: Generate response considering chunks as context using modular LLM generator
        provider = model_type or self.config.llm_provider
        logger.info(f"Step 6: Generating response with model_type: {provider}")
        response_text = self.generator.generate(
            query=query,
            context_chunks=retrieved_chunks,
            provider=provider
        )

        return {
            "query": query,
            "response": response_text,
            "context_chunks": retrieved_chunks,
            "chunks_count": len(retrieved_chunks),
            "provider": provider
        }

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on the current vector database and indexed files."""
        total_chunks = self.vector_store.count()
        return {
            "total_chunks": total_chunks,
            "indexed_files": len(self.indexed_files),
            "collection_name": self.config.collection_name,
            "embedding_model": self.config.embedding_model,
            "default_provider": self.config.llm_provider
        }

    def reset(self):
        """Reset the vector database collection and clear indexed documents."""
        self.vector_store.reset()
        self.indexed_files = []
