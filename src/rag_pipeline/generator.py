import os
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ModularGenerator:
    """
    Modular response generator supporting multiple LLM backends:
    - fallback: Offline extractive synthesizer (zero external dependencies/keys)
    - huggingface: Local HuggingFace transformers pipeline
    - gemini: Google Generative AI API (via GEMINI_API_KEY)
    - openai: OpenAI API (via OPENAI_API_KEY)

    Produces clean, structured outputs with emojis, bullet points, and bold highlights.
    """

    def __init__(
        self,
        default_provider: str = "fallback",
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        max_new_tokens: int = 350
    ):
        self.default_provider = default_provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self._hf_pipeline = None

    def build_prompt(self, query: str, context_chunks: List[str]) -> str:
        """Construct structured prompt enforcing emoji, bullet points, and clean formatting."""
        joined_context = "\n\n".join(
            f"[Context Chunk {i+1}]:\n{chunk.strip()}"
            for i, chunk in enumerate(context_chunks)
        )
        prompt = (
            f"You are a helpful and intelligent AI knowledge assistant. Answer the user question based strictly on the provided context.\n\n"
            f"IMPORTANT FORMATTING INSTRUCTIONS:\n"
            f"1. Start with a direct, concise answer titled with an emoji (e.g. 🎯 **Direct Answer:**).\n"
            f"2. Break down the explanation into clear, structured bullet points using emojis (e.g. 🔹, 🚀, 🛡️, ⚙️, 📌).\n"
            f"3. Highlight key terms and metrics in **bold**.\n"
            f"4. Add a concluding section with a key insight (e.g. 💡 **Key Takeaway:**).\n"
            f"5. If the context does not contain the answer, politely state: '❌ *The provided documents do not contain enough information to answer this question.*'\n\n"
            f"--- CONTEXT ---\n{joined_context}\n\n"
            f"--- QUESTION ---\n{query}\n\n"
            f"--- ANSWER ---"
        )
        return prompt

    def generate(
        self,
        query: str,
        context_chunks: List[Any],
        provider: Optional[str] = None
    ) -> str:
        """
        Generate response based on retrieved chunks and user query.
        """
        selected_provider = (provider or self.default_provider).lower()

        # Normalize chunks to list of strings
        text_chunks = []
        for chunk in context_chunks:
            if isinstance(chunk, dict):
                text_chunks.append(chunk.get("text", str(chunk)))
            else:
                text_chunks.append(str(chunk))

        if not text_chunks:
            return (
                "⚠️ **No Context Available**\n\n"
                "- ❌ No relevant context found for your query in the provided documents.\n"
                "- 💡 *Tip: Try uploading a document or loading the sample paper in the sidebar first.*"
            )

        prompt = self.build_prompt(query, text_chunks)

        if selected_provider in ("huggingface", "transformers"):
            return self._generate_huggingface(prompt, query, text_chunks)
        elif selected_provider == "gemini":
            return self._generate_gemini(prompt, query, text_chunks)
        elif selected_provider == "openai":
            return self._generate_openai(prompt, query, text_chunks)
        else:
            return self._generate_fallback(query, text_chunks)

    def _generate_fallback(self, query: str, text_chunks: List[str]) -> str:
        """
        Local extractive synthesis fallback.
        Produces beautifully structured Markdown with emojis and bullet points.
        """
        stopwords = {
            "what", "is", "are", "the", "a", "an", "of", "in", "to", "for",
            "with", "on", "at", "by", "from", "how", "why", "who", "which",
            "where", "when", "does", "do", "can", "could", "should", "would",
            "and", "or", "about", "tell", "me", "explain", "give"
        }
        query_words = [w.lower() for w in re.findall(r'\b\w+\b', query) if w.lower() not in stopwords]

        # Extract sentences from all chunks
        full_text = " ".join(text_chunks)
        raw_sentences = re.split(r'(?<=[.?!])\s+', full_text)
        
        scored_sentences = []
        seen = set()

        for s in raw_sentences:
            s_clean = s.strip()
            if len(s_clean) < 15:
                continue
            s_lower = s_clean.lower()
            if s_lower in seen:
                continue
            seen.add(s_lower)

            # Score by match count and word density
            matches = sum(1 for w in query_words if w in s_lower)
            if matches > 0:
                scored_sentences.append((matches, s_clean))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)

        emojis = ["🔹", "🚀", "📌", "🛡️", "⚙️", "✨", "📊"]

        if scored_sentences:
            top_matches = [s for _, s in scored_sentences[:5]]
            
            # Format primary answer and bullet points
            direct_answer = top_matches[0]
            bullet_points = []
            
            # Bold query terms in sentences for readability
            for idx, sentence in enumerate(top_matches):
                bullet_emoji = emojis[idx % len(emojis)]
                highlighted = sentence
                for qw in query_words:
                    pattern = re.compile(rf'\b({re.escape(qw)})\b', re.IGNORECASE)
                    highlighted = pattern.sub(r'**\1**', highlighted)
                bullet_points.append(f"{bullet_emoji} {highlighted}")

            bullets_formatted = "\n\n".join(bullet_points)

            response = (
                f"🎯 **Key Answer:**\n"
                f"> {direct_answer}\n\n"
                f"📋 **Detailed Highlights & Context:**\n\n"
                f"{bullets_formatted}\n\n"
                f"💡 **Key Takeaway:**\n"
                f"- Verified from **{len(text_chunks)} retrieved knowledge chunk(s)** matching your query: *'{query}'*."
            )
            return response
        else:
            # Fallback when exact keyword matches aren't segregated into sentences
            sample_bullets = []
            for i, chunk in enumerate(text_chunks[:3]):
                bullet_emoji = emojis[i % len(emojis)]
                cleaned_preview = chunk.strip().replace("\n", " ")
                if len(cleaned_preview) > 180:
                    cleaned_preview = cleaned_preview[:180].rstrip() + "..."
                sample_bullets.append(f"{bullet_emoji} {cleaned_preview}")

            bullets_text = "\n\n".join(sample_bullets)
            return (
                f"🔍 **Retrieved Relevant Information:**\n\n"
                f"{bullets_text}\n\n"
                f"💡 **Context Summary:**\n"
                f"- Extracted top **{len(text_chunks)} chunk(s)** from your indexed documents for question: *'{query}'*."
            )

    def _generate_huggingface(self, prompt: str, query: str, text_chunks: List[str]) -> str:
        try:
            from transformers import pipeline
            if self._hf_pipeline is None:
                model = self.model_name or "google/flan-t5-base"
                logger.info(f"Loading HuggingFace text2text-generation model: {model}")
                self._hf_pipeline = pipeline("text2text-generation", model=model, max_length=self.max_new_tokens)
            
            output = self._hf_pipeline(prompt)
            if output and len(output) > 0:
                raw = output[0].get("generated_text", "").strip()
                return (
                    f"🎯 **Generated Response (HuggingFace):**\n\n"
                    f"🔹 {raw}\n\n"
                    f"💡 **Context Grounding:**\n"
                    f"- Synthesized using **{len(text_chunks)} source chunk(s)**."
                )
        except Exception as e:
            logger.warning(f"HuggingFace generation failed: {e}. Falling back to extractive generator.")
        return self._generate_fallback(query, text_chunks)

    def _generate_gemini(self, prompt: str, query: str, text_chunks: List[str]) -> str:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("No GEMINI_API_KEY found in environment. Falling back to extractive generator.")
            return self._generate_fallback(query, text_chunks)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.model_name or "gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini API generation failed: {e}. Falling back to extractive generator.")
            return self._generate_fallback(query, text_chunks)

    def _generate_openai(self, prompt: str, query: str, text_chunks: List[str]) -> str:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No OPENAI_API_KEY found in environment. Falling back to extractive generator.")
            return self._generate_fallback(query, text_chunks)
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=self.model_name or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions using the provided context, formatting cleanly with emojis and bullet points."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_new_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI API generation failed: {e}. Falling back to extractive generator.")
            return self._generate_fallback(query, text_chunks)
