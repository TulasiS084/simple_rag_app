import uuid
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

# Normalize model name: user requested 'all-MiniLM-L8-v2' which is commonly mapped to all-MiniLM-L6-v2 or all-MiniLM-L12-v2
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def resolve_model_name(model_name: Optional[str]) -> str:
    if not model_name:
        return DEFAULT_EMBEDDING_MODEL
    name = model_name.strip()
    if "all-MiniLM-L8-v2" in name or "all-minilm-l8-v2" in name.lower():
        # Fall back gracefully to existing HF all-MiniLM-L6-v2 or user specified
        return "sentence-transformers/all-MiniLM-L6-v2"
    if not name.startswith("sentence-transformers/") and "/" not in name:
        return f"sentence-transformers/{name}"
    return name


class ChromaVectorStore:
    """ChromaDB vector store with sentence-transformers embedding support."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "rag_collection",
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.model_name = resolve_model_name(embedding_model_name)
        self._embedding_model = None
        self._client = None
        self._collection = None

        self._init_db()

    def _init_db(self):
        try:
            import chromadb
            from chromadb.config import Settings

            if self.persist_directory:
                self._client = chromadb.PersistentClient(path=self.persist_directory)
            else:
                self._client = chromadb.Client(Settings(is_persistent=False))

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.warning(f"ChromaDB initialization error: {e}. Running in in-memory fallback mode.")
            self._client = None
            self._collection = None
            self._in_memory_docs: List[Dict[str, Any]] = []

    def _get_embedding_model(self):
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(f"SentenceTransformer load warning: {e}. Using deterministic mock embedding.")
                self._embedding_model = "fallback"
        return self._embedding_model

    def _encode(self, texts: List[str]) -> List[List[float]]:
        model = self._get_embedding_model()
        if model != "fallback":
            return model.encode(texts).tolist()

        # Deterministic lightweight 384-d bag-of-words / hash embedding fallback
        import hashlib
        embeddings = []
        for text in texts:
            vec = [0.0] * 384
            words = text.lower().split()
            for w in words:
                h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
                idx = h % 384
                vec[idx] += 1.0
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            embeddings.append([x / norm for x in vec])
        return embeddings

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Embed and store chunks into ChromaDB.
        
        Args:
            chunks: List of chunk dictionaries containing 'chunk_id', 'text', and 'metadata'.
        """
        if not chunks:
            return

        ids = [chunk.get("chunk_id", str(uuid.uuid4())) for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        
        # Chroma requires primitive metadata values
        metadatas = []
        for chunk in chunks:
            raw_meta = chunk.get("metadata", {})
            clean_meta = {
                str(k): (v if isinstance(v, (str, int, float, bool)) else str(v))
                for k, v in raw_meta.items()
            }
            metadatas.append(clean_meta)

        embeddings = self._encode(texts)

        if self._collection is not None:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
        else:
            for i, (cid, txt, meta, emb) in enumerate(zip(ids, texts, metadatas, embeddings)):
                self._in_memory_docs.append({
                    "chunk_id": cid,
                    "text": txt,
                    "metadata": meta,
                    "embedding": emb
                })

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Query the vector store for the top-k nearest chunks.
        
        Args:
            query_text: The search query text.
            top_k: Number of top results to return.
            
        Returns:
            List of dictionaries with 'chunk_id', 'text', 'metadata', and 'score'.
        """
        query_embedding = self._encode([query_text])

        if self._collection is not None:
            results = self._collection.query(
                query_embeddings=query_embedding,
                n_results=top_k
            )

            output = []
            if not results["ids"] or not results["ids"][0]:
                return output

            for i in range(len(results["ids"][0])):
                score = None
                if "distances" in results and results["distances"] and results["distances"][0]:
                    score = float(results["distances"][0][i])
                output.append({
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": score
                })
            return output
        else:
            # Simple cosine similarity fallback
            def cosine_sim(a, b):
                dot = sum(x * y for x, y in zip(a, b))
                norm_a = sum(x * x for x in a) ** 0.5 or 1.0
                norm_b = sum(y * y for y in b) ** 0.5 or 1.0
                return dot / (norm_a * norm_b)

            q_vec = query_embedding[0]
            scored = []
            for doc in getattr(self, "_in_memory_docs", []):
                sim = cosine_sim(q_vec, doc["embedding"])
                scored.append({
                    "chunk_id": doc["chunk_id"],
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": round(1.0 - sim, 4)  # distance
                })
            scored.sort(key=lambda x: x["score"] if x["score"] is not None else 0)
            return scored[:top_k]

    def count(self) -> int:
        """Returns the number of documents in the collection."""
        if self._collection is not None:
            return self._collection.count()
        return len(getattr(self, "_in_memory_docs", []))

    def reset(self):
        """Resets/deletes the collection."""
        if self._collection is not None and self._client is not None:
            try:
                self._client.delete_collection(name=self.collection_name)
            except Exception:
                pass
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self._in_memory_docs = []
