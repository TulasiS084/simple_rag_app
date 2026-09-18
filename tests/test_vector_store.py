import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.rag_pipeline.vector_store import ChromaVectorStore, resolve_model_name
except ImportError:
    from rag_pipeline.vector_store import ChromaVectorStore, resolve_model_name

class TestVectorStore(unittest.TestCase):
    def setUp(self):
        # Use in-memory ChromaDB for testing
        self.store = ChromaVectorStore(persist_directory=None, collection_name="test_collection")
        self.store.reset()

    def test_resolve_model_name_alias(self):
        name = resolve_model_name("all-MiniLM-L8-v2")
        self.assertEqual(name, "sentence-transformers/all-MiniLM-L6-v2")
        
        name2 = resolve_model_name("sentence-transformers/all-MiniLM-L6-v2")
        self.assertEqual(name2, "sentence-transformers/all-MiniLM-L6-v2")

    def test_add_and_query_chunks(self):
        sample_chunks = [
            {
                "chunk_id": "chunk-1",
                "text": "The Python programming language was created by Guido van Rossum.",
                "metadata": {"source": "python_history.pdf", "page": 1}
            },
            {
                "chunk_id": "chunk-2",
                "text": "Retrieval-augmented generation enhances large language models with vector databases.",
                "metadata": {"source": "rag_paper.pdf", "page": 1}
            },
            {
                "chunk_id": "chunk-3",
                "text": "Chroma is the AI-native open-source embedding database.",
                "metadata": {"source": "chroma_docs.pdf", "page": 2}
            }
        ]

        self.store.add_chunks(sample_chunks)
        self.assertEqual(self.store.count(), 3)

        # Query for Chroma
        results = self.store.query("What is Chroma vector database?", top_k=2)
        self.assertGreaterEqual(len(results), 1)
        self.assertLessEqual(len(results), 2)
        
        # Check structure
        top_result = results[0]
        self.assertIn("chunk_id", top_result)
        self.assertIn("text", top_result)
        self.assertIn("metadata", top_result)
        self.assertIn("score", top_result)

if __name__ == "__main__":
    unittest.main()
