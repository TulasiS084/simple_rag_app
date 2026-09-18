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
        self.assertIn("STRICT FORMATTING & GROUNDING INSTRUCTIONS", prompt)

    def test_generate_fallback_with_context(self):
        chunks = [
            {"text": "Python is an interpreted, high-level, general-purpose programming language.", "metadata": {"source": "python.pdf"}},
            {"text": "Chroma is an open-source vector store designed for AI development.", "metadata": {"source": "chroma.pdf"}}
        ]
        response = self.generator.generate(
            query="What is Python?",
            context_chunks=chunks,
            provider="fallback"
        )
        self.assertIn("Python", response)
        self.assertIn("programming language", response)
        self.assertIn("🎯 **Direct Answer:**", response)
        self.assertIn("📋 **Key Evidence & Document Details:**", response)
        self.assertIn("💡 **Key Takeaway:**", response)

    def test_generate_empty_context(self):
        response = self.generator.generate(
            query="Tell me about quantum physics",
            context_chunks=[],
            provider="fallback"
        )
        self.assertIn("No relevant information found", response)

    def test_generate_irrelevant_query(self):
        chunks = [
            {"text": "Python is an interpreted, high-level, general-purpose programming language."},
            {"text": "Chroma is an open-source vector store designed for AI development."}
        ]
        response = self.generator.generate(
            query="What is quantum astrophysics?",
            context_chunks=chunks,
            provider="fallback"
        )
        expected_refusal = (
            "❌ **No relevant information found in the uploaded documents.**\n\n"
            "💡 *The provided document does not appear to discuss 'What is quantum astrophysics?'. "
            "Try asking a question about the topics covered in your document.*"
        )
        self.assertEqual(response, expected_refusal)

    def test_emoji_and_bullet_formatting(self):
        chunks = [
            {"text": "Retrieval-Augmented Generation (RAG) significantly reduces model hallucinations by grounding outputs on factual data.", "metadata": {"source": "rag_paper.pdf"}},
            {"text": "Vector databases like ChromaDB store dense embeddings calculated with all-MiniLM-L6-v2.", "metadata": {"source": "rag_paper.pdf"}}
        ]
        response = self.generator.generate(
            query="How does RAG reduce hallucinations?",
            context_chunks=chunks,
            provider="fallback"
        )
        # Verify emojis and new section headers are present
        self.assertTrue(any(e in response for e in ["🎯", "🔹", "📌", "💡", "🚀", "🛡️"]))
        self.assertIn("🎯 **Direct Answer:**", response)
        self.assertIn("📋 **Key Evidence & Document Details:**", response)
        self.assertIn("💡 **Key Takeaway:**", response)

    def test_no_direct_answer_repeated_in_bullets(self):
        chunks = [
            {"text": "Sentence A describes the primary definition of RAG systems. Sentence B provides performance statistics. Sentence C discusses security guarantees."}
        ]
        response = self.generator.generate(
            query="definition of RAG systems",
            context_chunks=chunks,
            provider="fallback"
        )
        self.assertIn("🎯 **Direct Answer:**", response)
        self.assertIn("📋 **Key Evidence & Document Details:**", response)

        # Extract direct answer and bullets section
        parts = response.split("📋 **Key Evidence & Document Details:**")
        direct_part = parts[0]
        bullets_part = parts[1].split("💡 **Key Takeaway:**")[0]

        # The primary sentence selected for direct answer must not be repeated verbatim in bullets
        direct_lines = [l.strip() for l in direct_part.split("\n") if l.strip() and not l.startswith("🎯")]
        if direct_lines:
            direct_text = direct_lines[0]
            self.assertNotIn(direct_text, bullets_part)

if __name__ == "__main__":
    unittest.main()
