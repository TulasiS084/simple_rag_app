import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.rag_pipeline.chunker import chunk_text, TextChunker
except ImportError:
    from rag_pipeline.chunker import chunk_text, TextChunker

class TestChunker(unittest.TestCase):
    def test_empty_text(self):
        chunks = chunk_text("")
        self.assertEqual(chunks, [])

    def test_chunk_size_and_overlap(self):
        text = (
            "Retrieval-augmented generation (RAG) is an AI framework for improving the quality "
            "of LLM responses by grounding the model on external sources of knowledge. "
            "This reduces hallucinations, ensures citations, and keeps models up to date."
        )
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk(text, metadata={"source": "test.pdf", "page": 1})
        
        self.assertTrue(len(chunks) >= 2)
        for c in chunks:
            self.assertIn("chunk_id", c)
            self.assertIn("text", c)
            self.assertIn("metadata", c)
            self.assertEqual(c["metadata"]["source"], "test.pdf")
            self.assertEqual(c["metadata"]["page"], 1)
            self.assertIn("chunk_index", c["metadata"])

    def test_single_word_larger_than_chunk_size(self):
        long_word = "A" * 150
        chunks = chunk_text(long_word, chunk_size=50, chunk_overlap=10)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["text"], long_word)

if __name__ == "__main__":
    unittest.main()
