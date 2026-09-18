import os
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

STOPWORDS = {
    "what", "is", "are", "the", "a", "an", "of", "in", "to", "for",
    "with", "on", "at", "by", "from", "how", "why", "who", "which",
    "where", "when", "does", "do", "can", "could", "should", "would",
    "and", "or", "about", "tell", "me", "explain", "give", "please",
    "it", "its", "they", "their", "them", "this", "that", "these", "those",
    "be", "been", "being", "have", "has", "had", "was", "were"
}

META_WORDS = {
    "paper", "papers", "document", "documents", "pdf", "pdfs",
    "file", "files", "article", "articles", "all", "about",
    "handbook", "handbooks", "text", "texts", "read", "reading",
    "say", "says", "said", "tell", "tells", "telling", "give", "gives", "given"
}

BOILERPLATE_PATTERNS = [
    r'\bimportant\s+note\b',
    r'\bdisclaimer\b',
    r'\bstarting\s+template\b',
    r'\btemplate\s+for\b',
    r'\bcopyright\b',
    r'©|\(c\)',
    r'\ball\s+rights\s+reserved\b',
    r'\blicen[sc]e\b',
    r'\blicen[sc]ed\s+under\b',
    r'\bterms\s+of\s+(use|service)\b',
    r'\bconfidential\b',
    r'\bdo\s+not\s+distribute\b',
    r'\bopen\s+source\s+licen[sc]e\b',
    r'\bthis\s+paper\s+is\s+a\s+template\b',
    r'\bsample\s+template\b',
    r'\bauthor\s+guidelines\b',
    r'\bplease\s+cite\s+this\s+article\b',
    r'\bproceedings\s+of\b',
    r'\bpublished\s+by\b',
    r'\bpeer-reviewed\b'
]

def is_boilerplate(text: str) -> bool:
    """Check if a line or sentence contains boilerplate disclaimers."""
    t_lower = text.lower().strip()
    return any(re.search(pat, t_lower) for pat in BOILERPLATE_PATTERNS)

def is_overview_query(query: str) -> bool:
    """
    Explicit detection for Document Overview / Thematic Queries such as:
    - 'what is this paper (all) about'
    - 'summarize this document'
    - 'what is this document about'
    - 'overview of this paper'
    - 'main topic of this paper'
    """
    q = query.strip().lower()

    overview_patterns = [
        r'\bwhat\s+(is|are)\s+(this|the|all\s+this|it)\s+(paper|document|pdf|file|article|text|handbook)?\s*(all\s+)?about\b',
        r'\bwhat\s+(is|are)\s+(it\s+|this\s+)?(all\s+)?about\b',
        r'\b(summarize|summarise)\s+(this|the|all)?\s*(paper|document|pdf|file|article|text|handbook|work)?\b',
        r'\b(summary|overview|synopsis|rundown)\s+of\s+(this|the)?\s*(paper|document|pdf|file|article|text|handbook|work)?\b',
        r'\b(give|provide|show)\s+(me\s+)?(an?\s+)?(overview|summary|brief|synopsis|rundown)\b',
        r'\b(main|primary|core|central|general)\s+(topic|topics|theme|themes|subject|subjects|purpose|idea|ideas)\b',
        r'\bwhat\s+does\s+(this|the)\s+(paper|document|pdf|file|article)\s+(cover|discuss|talk\s+about|describe)\b',
        r'\btell\s+me\s+about\s+(this|the)\s+(paper|document|pdf|file|article)\b',
        r'\bexplain\s+(this|the)\s+(paper|document|pdf|file|article)\b',
        r'\bwhat\s+is\s+(this|the)\s+(paper|document|pdf|file|article)\b',
    ]
    for pat in overview_patterns:
        if re.search(pat, q):
            return True

    words = re.findall(r'\b[a-zA-Z0-9_-]+\b', q)
    overview_indicators = {
        "overview", "summary", "summarize", "summarise", "topic", "topics",
        "theme", "themes", "subject", "subjects", "purpose", "discuss",
        "discusses", "cover", "covers", "outline", "synopsis", "about"
    }
    non_meta_non_stop = [
        w for w in words
        if w not in STOPWORDS and w not in META_WORDS and w not in overview_indicators and len(w) > 1
    ]

    if not non_meta_non_stop and any(w in (overview_indicators | META_WORDS) for w in words):
        if any(w in overview_indicators for w in words) or ("what" in words and "about" in words):
            return True

    return False


class ModularGenerator:
    """
    Modular response generator supporting multiple LLM backends:
    - fallback: Offline extractive passage synthesizer (zero external dependencies/keys)
    - huggingface: Local HuggingFace transformers pipeline
    - gemini: Google Generative AI API (via GEMINI_API_KEY)
    - openai: OpenAI API (via OPENAI_API_KEY)

    Produces clean, structured, document-grounded outputs with emojis,
    bullet points, bold highlights, and direct source attribution.
    """

    is_overview_query = staticmethod(is_overview_query)

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
        """Construct structured prompt enforcing strict document grounding, emojis, bullet points, and clean formatting."""
        joined_context = "\n\n".join(
            f"[Context Chunk {i+1}]:\n{chunk.strip()}"
            for i, chunk in enumerate(context_chunks)
        )
        if self.is_overview_query(query):
            instructions = (
                "STRICT FORMATTING & GROUNDING INSTRUCTIONS:\n"
                "1. 🎯 **Direct Answer:** Provide a crisp, concise direct answer identifying the actual subject matter and purpose of the document based on its Title, Abstract, or Introduction. Filter out boilerplate disclaimers (e.g. 'Important Note', 'Disclaimer', 'Starting template', 'Copyright', 'License').\n"
                "2. 📋 **Key Topics & Sections Covered:** Extract 2-4 distinct main themes or section headings from the document with bullet points using emojis (🔹, 🚀, 📌, 🛡️).\n"
                "3. Highlight key entities and technical terms in **bold**.\n"
                "4. 💡 **Key Takeaway:** Conclude with a brief takeaway citing relevance to the query.\n"
                "5. If the provided context does not contain sufficient facts to answer the question, do not attempt to guess. Instead respond exactly with:\n"
                f"❌ **No relevant information found in the uploaded documents.**\n\n💡 *The provided document does not appear to discuss '{query}'. Try asking a question about the topics covered in your document.*\n\n"
            )
        else:
            instructions = (
                "STRICT FORMATTING & GROUNDING INSTRUCTIONS:\n"
                "1. 🎯 **Direct Answer:** Provide a crisp, concise, highly accurate direct answer based solely on the document facts.\n"
                "2. 📋 **Key Evidence & Document Details:** Present 2-4 distinct, non-repetitive bullet points with supporting facts from the context using emojis (🔹, 🚀, 📌, 🛡️). Do not repeat the direct answer.\n"
                "3. Highlight key entities, metrics, and technical terms in **bold**.\n"
                "4. 💡 **Key Takeaway:** Conclude with a brief takeaway citing relevance to the query.\n"
                "5. If the provided context does not contain sufficient facts to answer the question, do not attempt to guess. Instead respond exactly with:\n"
                f"❌ **No relevant information found in the uploaded documents.**\n\n💡 *The provided document does not appear to discuss '{query}'. Try asking a question about the topics covered in your document.*\n\n"
            )

        prompt = (
            "You are a strict, truthful AI knowledge assistant grounded entirely in provided reference documents.\n"
            "Answer the user question based ONLY and STRICTLY on the facts directly stated in the context chunks below.\n"
            "DO NOT assume, extrapolate, speculate, or fabricate any facts not explicitly present in the text.\n\n"
            f"{instructions}"
            f"--- CONTEXT ---\n{joined_context}\n\n"
            f"--- QUESTION ---\n{query}\n\n"
            f"--- GROUNDED ANSWER ---"
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
                f"❌ **No relevant information found in the uploaded documents.**\n\n"
                f"💡 *The provided document does not appear to discuss '{query}'. "
                f"Try asking a question about the topics covered in your document.*"
            )

        prompt = self.build_prompt(query, text_chunks)

        if selected_provider in ("huggingface", "transformers"):
            return self._generate_huggingface(prompt, query, text_chunks, raw_chunks=context_chunks)
        elif selected_provider == "gemini":
            return self._generate_gemini(prompt, query, text_chunks, raw_chunks=context_chunks)
        elif selected_provider == "openai":
            return self._generate_openai(prompt, query, text_chunks, raw_chunks=context_chunks)
        else:
            return self._generate_fallback(query, text_chunks, raw_chunks=context_chunks)

    def _generate_overview_response(
        self,
        query: str,
        text_chunks: List[str],
        raw_chunks: Optional[List[Any]] = None
    ) -> str:
        """
        Generate high-accuracy response for Document Overview / Thematic Queries.
        - Prioritizes Title, Abstract, Introduction, and section headings
        - Filters out boilerplate disclaimers (Important Note, Disclaimer, Template, Copyright, License)
        - Formulates accurate Direct Answer identifying actual subject matter and purpose
        - Extracts 2-4 distinct main themes or section headings for Key Topics & Sections Covered
        """
        if not text_chunks:
            return (
                f"❌ **No relevant information found in the uploaded documents.**\n\n"
                f"💡 *The provided document does not appear to discuss '{query}'. "
                f"Try asking a question about the topics covered in your document.*"
            )

        # 1. Order chunks to prioritize document start (chunk_index == 0 or page == 1)
        paired = list(zip(raw_chunks, text_chunks)) if raw_chunks else [(None, c) for c in text_chunks]

        def chunk_order_key(item):
            raw, _ = item
            if isinstance(raw, dict):
                meta = raw.get("metadata", {})
                page = meta.get("page", 9999)
                idx = meta.get("chunk_index", 9999)
                return (page, idx)
            return (9999, 9999)

        sorted_pairs = sorted(paired, key=chunk_order_key)
        ordered_chunks = [txt for _, txt in sorted_pairs]

        # 2. Filter out boilerplate disclaimers from chunks
        clean_chunks = []
        for chunk in ordered_chunks:
            lines = [l for l in chunk.split("\n") if not is_boilerplate(l)]
            clean = "\n".join(lines).strip()
            if clean:
                clean_chunks.append(clean)
        if not clean_chunks:
            clean_chunks = ordered_chunks

        # Helper: text similarity
        def is_similar(t1: str, t2: str) -> bool:
            s1 = t1.lower().strip()
            s2 = t2.lower().strip()
            if s1 == s2 or s1 in s2 or s2 in s1:
                return True
            w1 = set(re.findall(r'\b\w+\b', s1))
            w2 = set(re.findall(r'\b\w+\b', s2))
            if not w1 or not w2:
                return False
            jaccard = len(w1 & w2) / len(w1 | w2)
            return jaccard > 0.55

        # 3. Extract Document Title
        title = None
        if clean_chunks:
            first_lines = [l.strip() for l in clean_chunks[0].split("\n") if l.strip()]
            for line in first_lines[:6]:
                if is_boilerplate(line):
                    continue
                if len(line) < 4 or line.isdigit():
                    continue
                if re.match(r'^(page\s+\d+|http|www|draft|confidential|abstract\b|\d+[\.\)]|\bchapter\b|\bsection\b)', line, re.IGNORECASE):
                    continue
                if len(line) <= 160:
                    title = line.strip("#* ")
                    break

        # 4. Extract Abstract / Introduction / Core Subject Matter Passage
        abstract_text = None
        intro_text = None
        for chunk in clean_chunks:
            if not abstract_text:
                m_abs = re.search(r'(?:^|\n)\s*Abstract(?:\s*[:\-—]|\s*\n)\s*(.*?)(?=(?:\n\s*\n|\n(?:\d+[\.\)]|\bIntroduction\b|[A-Z]{3,})|\Z))', chunk, re.IGNORECASE | re.DOTALL)
                if m_abs:
                    cand = m_abs.group(1).strip()
                    if len(cand) > 20 and not is_boilerplate(cand):
                        abstract_text = cand
            if not intro_text:
                m_intro = re.search(r'(?:^|\n)\s*(?:\d+[\.\)]\s*)?Introduction(?:\s+to\s+[^\n]+)?(?:\s*[:\-—]|\s*\n)\s*(.*?)(?=(?:\n\s*\n(?:\d+[\.\)]|[A-Z])|\Z))', chunk, re.IGNORECASE | re.DOTALL)
                if m_intro:
                    cand = m_intro.group(1).strip()
                    if len(cand) > 20 and not is_boilerplate(cand):
                        intro_text = cand

        def extract_sentences_from_text(txt: str, max_sents: int = 2) -> str:
            raw_s = re.split(r'(?<=[.?!])\s+|\n+', txt)
            good_sents = []
            for s in raw_s:
                c = re.sub(r'^[-*•\d\.\)]+\s*', '', s).strip()
                if len(c) >= 25 and not is_boilerplate(c):
                    if title and c.lower() == title.lower():
                        continue
                    good_sents.append(c)
                    if len(good_sents) >= max_sents:
                        break
            return " ".join(good_sents)

        if abstract_text:
            core_passage = extract_sentences_from_text(abstract_text, 2) or abstract_text[:280]
        elif intro_text:
            core_passage = extract_sentences_from_text(intro_text, 2) or intro_text[:280]
        else:
            core_passage = extract_sentences_from_text(clean_chunks[0], 2)

        # Fallback if core_passage is still empty
        if not core_passage:
            for c in clean_chunks:
                core_passage = extract_sentences_from_text(c, 2)
                if core_passage:
                    break

        if not core_passage:
            core_passage = "This document presents structured technical and domain information."

        # Formulate Direct Answer identifying actual subject matter and purpose
        if title and not core_passage.lower().startswith(title.lower()):
            direct_answer = f"This document focuses on **{title}**. {core_passage}"
        else:
            direct_answer = core_passage

        # 5. Extract 2-4 distinct main themes or section headings
        topics = []
        seen_headings = set()

        def add_topic(heading: str, summary: str):
            h_clean = heading.strip().strip("#*:").strip()
            h_display = re.sub(r'^(?:(?:\d+|[IVXLCDM]+)[\.\)]\s*|Step\s+\d+:\s*)', '', h_clean).strip()
            if not h_display or is_boilerplate(h_display) or len(h_display) < 3:
                return
            h_lower = h_display.lower()
            if h_lower in seen_headings or any(is_similar(h_lower, s) for s in seen_headings):
                return
            s_clean = summary.strip() if summary else ""
            if s_clean and is_boilerplate(s_clean):
                s_clean = ""
            seen_headings.add(h_lower)
            topics.append((h_display, s_clean))

        # Check numbered section headings (e.g. "1. Introduction to RAG", "2. Benefits of RAG")
        numbered_pattern = re.compile(r'(?:^|\n)(?:(?:\d+|[IVXLCDM]+)[\.\)]\s+)([A-Z][^\n]{2,60})', re.MULTILINE)
        for chunk in clean_chunks:
            for match in numbered_pattern.finditer(chunk):
                heading = match.group(1)
                after_text = chunk[match.end():]
                following_lines = [l.strip() for l in after_text.split("\n") if l.strip()]
                summary = ""
                if following_lines:
                    first_line = following_lines[0]
                    if not is_boilerplate(first_line) and not re.match(r'^(?:\d+|[IVXLCDM]+)[\.\)]', first_line):
                        summary = re.sub(r'^[-*•]\s*', '', first_line)
                        summary = re.split(r'(?<=[.?!])\s+', summary)[0]
                add_topic(heading, summary)
                if len(topics) >= 4:
                    break
            if len(topics) >= 4:
                break

        # Check Markdown headings (e.g. "## Heading")
        if len(topics) < 4:
            md_pattern = re.compile(r'(?:^|\n)#{1,4}\s+([A-Z][^\n]{2,60})', re.MULTILINE)
            for chunk in clean_chunks:
                for match in md_pattern.finditer(chunk):
                    heading = match.group(1)
                    after_text = chunk[match.end():]
                    following_lines = [l.strip() for l in after_text.split("\n") if l.strip()]
                    summary = ""
                    if following_lines:
                        first_line = following_lines[0]
                        if not is_boilerplate(first_line) and not first_line.startswith("#"):
                            summary = re.split(r'(?<=[.?!])\s+', re.sub(r'^[-*•]\s*', '', first_line))[0]
                    add_topic(heading, summary)
                    if len(topics) >= 4:
                        break
                if len(topics) >= 4:
                    break

        # Check colon headers (e.g. "- Reduced Hallucination: Grounding answers...")
        if len(topics) < 2:
            colon_pattern = re.compile(r'(?:^|\n)[-*•]?\s*([A-Z][A-Za-z0-9\s-]{2,40}):\s*([^\n]{10,120})', re.MULTILINE)
            for chunk in clean_chunks:
                for match in colon_pattern.finditer(chunk):
                    heading = match.group(1)
                    summary = match.group(2)
                    add_topic(heading, summary)
                    if len(topics) >= 4:
                        break
                if len(topics) >= 4:
                    break

        # Fallback if fewer than 2 topics: extract distinct informative sentences across chunks
        if len(topics) < 2:
            for chunk in clean_chunks:
                sents = [s.strip() for s in re.split(r'(?<=[.?!])\s+|\n+', chunk) if len(s.strip()) > 30]
                for sent in sents:
                    clean_s = re.sub(r'^[-*•\d\.\)]+\s*', '', sent).strip()
                    if is_boilerplate(clean_s) or is_similar(clean_s, direct_answer):
                        continue
                    words = clean_s.split()
                    if len(words) > 5:
                        theme_title = " ".join(words[:4]).rstrip(",.:;-")
                        add_topic(theme_title, clean_s)
                    if len(topics) >= 2:
                        break
                if len(topics) >= 2:
                    break

        # Format 2-4 topics with emojis
        bullet_emojis = ["🔹", "📌", "🚀", "🛡️"]
        formatted_bullets = []
        for idx, (heading, summary) in enumerate(topics[:4]):
            emoji = bullet_emojis[idx % len(bullet_emojis)]
            if summary and not is_similar(heading, summary):
                if len(summary) > 160:
                    summary = summary[:157] + "..."
                formatted_bullets.append(f"{emoji} **{heading}:** {summary}")
            else:
                formatted_bullets.append(f"{emoji} **{heading}**")

        if not formatted_bullets:
            formatted_bullets.append("🔹 **Document Overview:** Comprehensive overview of document structure and core topics.")

        topics_str = "\n\n".join(formatted_bullets)

        # 6. Citations and Key Takeaway
        sources = []
        if raw_chunks:
            for c in raw_chunks:
                if isinstance(c, dict):
                    src = c.get("metadata", {}).get("source")
                    if src and str(src) not in sources:
                        sources.append(str(src))

        if sources:
            source_citation = f"source: **{', '.join(sources)}**"
        else:
            source_citation = "uploaded document knowledge base"

        takeaway = (
            f"💡 **Key Takeaway:**\n"
            f"- Grounded directly in factual evidence from {source_citation} "
            f"providing a thematic overview across **{len(text_chunks)} retrieved knowledge chunk(s)**."
        )

        return (
            f"🎯 **Direct Answer:**\n"
            f"{direct_answer}\n\n"
            f"📋 **Key Topics & Sections Covered:**\n\n"
            f"{topics_str}\n\n"
            f"{takeaway}"
        )

    def _generate_fallback(
        self,
        query: str,
        text_chunks: List[str],
        raw_chunks: Optional[List[Any]] = None
    ) -> str:
        """
        Intelligent, document-grounded extractive passage synthesizer.
        Preserves top-scoring semantic chunks retrieved from ChromaDB,
        identifies the primary continuous passage for direct answering,
        extracts distinct non-repetitive supporting facts with emojis,
        and provides source-attributed takeaways.
        """
        if not text_chunks:
            return (
                f"❌ **No relevant information found in the uploaded documents.**\n\n"
                f"💡 *The provided document does not appear to discuss '{query}'. "
                f"Try asking a question about the topics covered in your document.*"
            )

        # Check for Document Overview / Thematic Queries
        if self.is_overview_query(query):
            return self._generate_overview_response(query, text_chunks, raw_chunks=raw_chunks)

        stopwords = STOPWORDS

        query_words = [
            w.lower() for w in re.findall(r'\b[a-zA-Z0-9_-]+\b', query)
            if w.lower() not in stopwords and w.lower() not in META_WORDS and len(w) > 1
        ]

        def term_matches(term: str, text_lower: str) -> bool:
            if term in text_lower:
                return True
            if len(term) > 4:
                for suffix in ('ing', 'tion', 'tions', 'ed', 'es', 's'):
                    if term.endswith(suffix):
                        stem = term[:-len(suffix)]
                        if len(stem) >= 3 and stem in text_lower:
                            return True
            return False

        # Check if retrieved chunks contain any information addressing the query
        has_relevant_info = False
        if query_words:
            for chunk in text_chunks:
                chunk_lower = chunk.lower()
                if any(term_matches(qw, chunk_lower) for qw in query_words):
                    has_relevant_info = True
                    break
        else:
            has_relevant_info = True

        if not has_relevant_info:
            return (
                f"❌ **No relevant information found in the uploaded documents.**\n\n"
                f"💡 *The provided document does not appear to discuss '{query}'. "
                f"Try asking a question about the topics covered in your document.*"
            )

        # Extract sentences by chunk, preserving original semantic ranking order
        chunk_sentences = []  # (c_idx, s_idx, sentence_str)
        for c_idx, chunk in enumerate(text_chunks):
            # Split sentences on .?! followed by space/newline, or raw newlines
            raw_sents = re.split(r'(?<=[.?!])\s+|\n+', chunk)
            s_idx = 0
            for s in raw_sents:
                clean = s.strip()
                # Strip leading list markers or numbers (e.g. "- ", "* ", "1. ")
                clean = re.sub(r'^[-*•\d\.\)]+\s*', '', clean).strip()
                if len(clean) >= 20 and not is_boilerplate(clean):
                    chunk_sentences.append((c_idx, s_idx, clean))
                    s_idx += 1

        if not chunk_sentences:
            for c_idx, chunk in enumerate(text_chunks):
                clean = chunk.strip().replace("\n", " ")
                if clean and not is_boilerplate(clean):
                    chunk_sentences.append((c_idx, 0, clean))

        # Sentence scoring function favoring top semantic chunks & query relevance
        def score_sentence(c_idx: int, s_idx: int, sent: str) -> float:
            s_lower = sent.lower()
            # Base semantic score directly reflects ChromaDB's all-MiniLM-L6-v2 ranking
            base_score = max(0.5, 6.0 - (c_idx * 1.5))

            # Query keyword matches
            exact_matches = 0
            stem_matches = 0
            for qw in query_words:
                if re.search(rf'\b{re.escape(qw)}\b', s_lower):
                    exact_matches += 1
                elif term_matches(qw, s_lower):
                    stem_matches += 1

            match_score = (exact_matches * 4.0) + (stem_matches * 2.0)

            # Position bonus within the chunk (first sentence is often the thesis/definition)
            position_bonus = 2.0 if s_idx == 0 else (1.0 if s_idx == 1 else 0.0)

            # Length appropriateness bonus (favor complete, informative sentences)
            length_bonus = 1.5 if 35 <= len(sent) <= 280 else (0.0 if len(sent) < 35 else -1.0)

            return base_score + match_score + position_bonus + length_bonus

        scored_sentences = [
            (score_sentence(c, s, sent), c, s, sent)
            for c, s, sent in chunk_sentences
        ]
        scored_sentences.sort(key=lambda x: x[0], reverse=True)

        # Helper: Similarity check to prevent repetition
        def is_similar(t1: str, t2: str) -> bool:
            s1 = t1.lower().strip()
            s2 = t2.lower().strip()
            if s1 == s2 or s1 in s2 or s2 in s1:
                return True
            w1 = set(re.findall(r'\b\w+\b', s1))
            w2 = set(re.findall(r'\b\w+\b', s2))
            if not w1 or not w2:
                return False
            jaccard = len(w1 & w2) / len(w1 | w2)
            return jaccard > 0.55

        # 1. Select Direct Answer from the top-scoring semantic chunk (c_idx == 0)
        chunk_0_scored = [item for item in scored_sentences if item[1] == 0]
        direct_candidate = None
        if chunk_0_scored:
            # Check if any sentence in chunk 0 has a query match
            chunk_0_matches = [
                item for item in chunk_0_scored
                if any(term_matches(qw, item[3].lower()) for qw in query_words)
            ]
            if chunk_0_matches:
                direct_candidate = chunk_0_matches[0]
            else:
                direct_candidate = chunk_0_scored[0]
        else:
            direct_candidate = scored_sentences[0]

        direct_c_idx = direct_candidate[1]
        direct_s_idx = direct_candidate[2]
        direct_answer = direct_candidate[3]

        # Check if immediately following sentence in the same chunk forms a natural continuous passage
        next_sentences = [
            sent for (c, s, sent) in chunk_sentences
            if c == direct_c_idx and s == direct_s_idx + 1
        ]
        if next_sentences and len(direct_answer) < 140:
            next_sent = next_sentences[0]
            if len(direct_answer) + len(next_sent) <= 280 and not is_similar(direct_answer, next_sent):
                direct_answer = f"{direct_answer} {next_sent}"

        # 2. Extract 2-4 distinct, non-repetitive key supporting evidence bullets
        # MUST NOT repeat the direct answer sentence!
        candidate_bullets = []
        for score, c, s, sent in scored_sentences:
            if is_similar(sent, direct_answer):
                continue
            if any(is_similar(sent, b) for b in candidate_bullets):
                continue
            candidate_bullets.append(sent)
            if len(candidate_bullets) >= 4:
                break

        # If fewer than 2 bullets found, look for any remaining unique informative sentences
        if len(candidate_bullets) < 2:
            for c, s, sent in chunk_sentences:
                if is_similar(sent, direct_answer):
                    continue
                if any(is_similar(sent, b) for b in candidate_bullets):
                    continue
                candidate_bullets.append(sent)
                if len(candidate_bullets) >= 2:
                    break

        bullet_emojis = ["🔹", "🚀", "📌", "🛡️"]
        formatted_bullets = []
        for idx, bullet_text in enumerate(candidate_bullets):
            emoji = bullet_emojis[idx % len(bullet_emojis)]
            highlighted = bullet_text
            for qw in query_words:
                pattern = re.compile(rf'\b({re.escape(qw)})\b', re.IGNORECASE)
                highlighted = pattern.sub(r'**\1**', highlighted)
            formatted_bullets.append(f"{emoji} {highlighted}")

        if not formatted_bullets:
            formatted_bullets.append("🔹 Grounded in verified document context matching query terms.")

        bullets_str = "\n\n".join(formatted_bullets)

        # 3. Formulate Key Takeaway citing document source and relevance
        sources = []
        if raw_chunks:
            for c in raw_chunks:
                if isinstance(c, dict):
                    src = c.get("metadata", {}).get("source")
                    if src and str(src) not in sources:
                        sources.append(str(src))

        if sources:
            source_citation = f"source: **{', '.join(sources)}**"
        else:
            source_citation = "uploaded document knowledge base"

        takeaway = (
            f"💡 **Key Takeaway:**\n"
            f"- Grounded directly in factual evidence from {source_citation} "
            f"across **{len(text_chunks)} retrieved knowledge chunk(s)** matching *'{query}'*."
        )

        return (
            f"🎯 **Direct Answer:**\n"
            f"{direct_answer}\n\n"
            f"📋 **Key Evidence & Document Details:**\n\n"
            f"{bullets_str}\n\n"
            f"{takeaway}"
        )

    def _generate_huggingface(self, prompt: str, query: str, text_chunks: List[str], raw_chunks: Optional[List[Any]] = None) -> str:
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
                    f"🎯 **Direct Answer:**\n\n"
                    f"🔹 {raw}\n\n"
                    f"💡 **Key Takeaway:**\n"
                    f"- Synthesized strictly from **{len(text_chunks)} source chunk(s)**."
                )
        except Exception as e:
            logger.warning(f"HuggingFace generation failed: {e}. Falling back to extractive generator.")
        return self._generate_fallback(query, text_chunks, raw_chunks=raw_chunks)

    def _generate_gemini(self, prompt: str, query: str, text_chunks: List[str], raw_chunks: Optional[List[Any]] = None) -> str:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("No GEMINI_API_KEY found in environment. Falling back to extractive generator.")
            return self._generate_fallback(query, text_chunks, raw_chunks=raw_chunks)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                self.model_name or "gemini-1.5-flash",
                system_instruction="You are a strict, truthful document-grounded assistant. Answer solely based on provided context. Do not extrapolate."
            )
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini API generation failed: {e}. Falling back to extractive generator.")
            return self._generate_fallback(query, text_chunks, raw_chunks=raw_chunks)

    def _generate_openai(self, prompt: str, query: str, text_chunks: List[str], raw_chunks: Optional[List[Any]] = None) -> str:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No OPENAI_API_KEY found in environment. Falling back to extractive generator.")
            return self._generate_fallback(query, text_chunks, raw_chunks=raw_chunks)
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=self.model_name or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a truthful, strictly document-grounded assistant. Answer questions using ONLY the provided context without hallucinating or adding unverified external knowledge. Format with emojis and bullet points as instructed."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_new_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI API generation failed: {e}. Falling back to extractive generator.")
            return self._generate_fallback(query, text_chunks, raw_chunks=raw_chunks)
