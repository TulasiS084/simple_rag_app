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
        self.assertGreater(ingest_res["chunks_count"], 0)
        self.assertGreater(ingest_res["total_chars"], 0)
        self.assertGreater(ingest_res["chars"], 0)
        self.assertGreater(ingest_res["total_words"], 0)
        self.assertGreater(ingest_res["words"], 0)
        self.assertGreater(ingest_res["pages_count"], 0)
        self.assertGreater(ingest_res["pages_processed"], 0)
        self.assertTrue(len(ingest_res["text_preview"]) > 0)
        self.assertTrue(len(ingest_res["preview"]) > 0)
        self.assertTrue(len(ingest_res["full_text"]) > 0)

        # Verify self.pipeline.indexed_files
        self.assertEqual(len(self.pipeline.indexed_files), 1)
        stat = self.pipeline.indexed_files[0]
        self.assertEqual(stat["filename"], os.path.basename(self.pdf_path))
        self.assertEqual(stat["text_preview"], ingest_res["text_preview"])
        self.assertEqual(stat["full_text"], ingest_res["full_text"])
        self.assertEqual(stat["total_chars"], ingest_res["total_chars"])
        self.assertEqual(stat["total_words"], ingest_res["total_words"])
        self.assertEqual(stat["pages_count"], ingest_res["pages_count"])
        self.assertEqual(stat["chunks_count"], ingest_res["chunks_count"])

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
        self.assertIn("text_preview", res)
        self.assertIn("full_text", res)
        self.assertIn("ChromaDB", res["full_text"])

        # Verify indexed_files updated
        self.assertTrue(any(f["filename"] == "notes.txt" for f in self.pipeline.indexed_files))

        q_res = self.pipeline.query("What is ChromaDB used for?", top_k=1)
        self.assertIn("ChromaDB", q_res["response"])

    def test_ingest_blank_pdf_raises_value_error(self):
        blank_path = os.path.join(self.temp_dir.name, "empty_scanned.pdf")
        pdf_content = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
            b"xref\n0 4\n"
            b"0000000000 65535 f \n"
            b"0000000010 00000 n \n"
            b"0000000060 00000 n \n"
            b"0000000117 00000 n \n"
            b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
            b"startxref\n190\n%%EOF\n"
        )
        with open(blank_path, "wb") as f:
            f.write(pdf_content)

        filename = os.path.basename(blank_path)
        expected_msg = (
            f"No extractable text found in '{filename}'. "
            "This PDF may be a scanned image without an OCR layer or encrypted. "
            "Please provide a document with selectable text."
        )
        with self.assertRaises(ValueError) as ctx:
            self.pipeline.ingest(blank_path)
        self.assertEqual(str(ctx.exception), expected_msg)

    def test_query_empty_error(self):
        with self.assertRaises(ValueError):
            self.pipeline.query("")

if __name__ == "__main__":
    unittest.main()
