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

    def test_default_parameters(self):
        chunker = TextChunker()
        self.assertEqual(chunker.chunk_size, 1000)
        self.assertEqual(chunker.chunk_overlap, 150)

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

    def test_paragraph_and_sentence_boundary_preservation(self):
        para1 = "Artificial intelligence transforms software development. How does it work? It relies on neural models!"
        para2 = "Vector databases enable rapid semantic indexing. ChromaDB is a popular embedded vector store."
        full_text = f"{para1}\n\n{para2}"

        # With default size 1000, both paragraphs fit in one chunk and retain paragraph break
        chunks = chunk_text(full_text, chunk_size=1000, chunk_overlap=150)
        self.assertEqual(len(chunks), 1)
        self.assertIn("\n\n", chunks[0]["text"])
        self.assertIn("?", chunks[0]["text"])
        self.assertIn("!", chunks[0]["text"])

        # With smaller chunk size forcing split at sentence boundary
        chunker = TextChunker(chunk_size=120, chunk_overlap=30)
        split_chunks = chunker.chunk(full_text)
        self.assertTrue(len(split_chunks) >= 2)
        # Verify no chunk ends or starts with a truncated word
        for c in split_chunks:
            self.assertFalse(c["text"].startswith(" "))
            self.assertFalse(c["text"].endswith(" "))

if __name__ == "__main__":
    unittest.main()
