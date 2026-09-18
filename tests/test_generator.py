import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.rag_pipeline.generator import ModularGenerator
except ImportError:
    from rag_pipeline.generator import ModularGenerator

class TestModularGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ModularGenerator(default_provider="fallback")

    def test_build_prompt(self):
        chunks = ["RAG stands for retrieval-augmented generation.", "It grounds models on facts."]
        prompt = self.generator.build_prompt("What is RAG?", chunks)
        self.assertIn("RAG stands for", prompt)
        self.assertIn("What is RAG?", prompt)
        self.assertIn("--- CONTEXT ---", prompt)

    def test_generate_fallback_with_context(self):
        chunks = [
            {"text": "Python is an interpreted, high-level, general-purpose programming language."},
            {"text": "Chroma is an open-source vector store designed for AI development."}
        ]
        response = self.generator.generate(
            query="What is Python?",
            context_chunks=chunks,
            provider="fallback"
        )
        self.assertIn("Python", response)
        self.assertIn("programming language", response)

    def test_generate_empty_context(self):
        response = self.generator.generate(
            query="Tell me about quantum physics",
            context_chunks=[],
            provider="fallback"
        )
        self.assertIn("No relevant context found", response)

    def test_emoji_and_bullet_formatting(self):
        chunks = [
            {"text": "Retrieval-Augmented Generation (RAG) significantly reduces model hallucinations by grounding outputs on factual data."},
            {"text": "Vector databases like ChromaDB store dense embeddings calculated with all-MiniLM-L6-v2."}
        ]
        response = self.generator.generate(
            query="How does RAG reduce hallucinations?",
            context_chunks=chunks,
            provider="fallback"
        )
        # Verify emojis and bullet points are present
        self.assertTrue(any(e in response for e in ["🎯", "🔹", "📌", "💡"]))
        self.assertIn("🎯 **Key Answer:**", response)
        self.assertIn("📋 **Detailed Highlights & Context:**", response)

if __name__ == "__main__":
    unittest.main()
