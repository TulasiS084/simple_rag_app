import unittest
import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.rag_pipeline.pipeline import RAGPipeline
    from src.rag_pipeline.config import RAGConfig
    from src.create_sample_pdf import generate_sample_pdf
except ImportError:
    from rag_pipeline.pipeline import RAGPipeline
    from rag_pipeline.config import RAGConfig
    from create_sample_pdf import generate_sample_pdf

class TestRAGPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate temporary sample PDF
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.pdf_path = os.path.join(cls.temp_dir.name, "test_doc.pdf")
        generate_sample_pdf(cls.pdf_path)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def setUp(self):
        config = RAGConfig(
            chroma_db_dir=None,  # in-memory for testing
            collection_name="pipeline_test_collection",
            llm_provider="fallback"
        )
        self.pipeline = RAGPipeline(config)

    def test_ingest_and_query_pipeline(self):
        # Test Step 1, 2, 3: Ingest
        ingest_res = self.pipeline.ingest(self.pdf_path, chunk_size=300, chunk_overlap=30)
        self.assertEqual(ingest_res["status"], "success")
        self.assertGreater(ingest_res["chunks_processed"], 0)

        # Test Step 4, 5, 6: Query
        query_res = self.pipeline.query("What are the benefits of RAG?", top_k=2)
        self.assertIn("response", query_res)
        self.assertIn("context_chunks", query_res)
        self.assertEqual(len(query_res["context_chunks"]), 2)
        self.assertTrue(len(query_res["response"]) > 0)

    def test_ingest_text_document(self):
        txt_path = os.path.join(self.temp_dir.name, "notes.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("ChromaDB is a database for building AI applications with embeddings and LLMs.")
        res = self.pipeline.ingest(txt_path)
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["chunks_processed"], 0)

        q_res = self.pipeline.query("What is ChromaDB used for?", top_k=1)
        self.assertIn("ChromaDB", q_res["response"])

    def test_query_empty_error(self):
        with self.assertRaises(ValueError):
            self.pipeline.query("")

if __name__ == "__main__":
    unittest.main()
