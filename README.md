# Simple RAG Pipeline

A lightweight, robust, end-to-end **Retrieval-Augmented Generation (RAG)** pipeline built in Python with **ChromaDB**, **sentence-transformers**, and modular LLM backends.

---

## 🚀 Overview & RAG Operations

This project implements the complete 6-step RAG workflow requested:

| Step | Operation | Component | Implementation |
|---|---|---|---|
| **Step 1** | Read text data from input PDF | [`src/rag_pipeline/pdf_reader.py`](file:///C:/Users/Tulasi%20S/OneDrive/Desktop/rag/src/rag_pipeline/pdf_reader.py) | `PDFReader` extracts page-by-page text cleanly, preserving page metadata. |
| **Step 2** | Convert text data into chunks | [`src/rag_pipeline/chunker.py`](file:///C:/Users/Tulasi%20S/OneDrive/Desktop/rag/src/rag_pipeline/chunker.py) | `TextChunker` creates sliding-window chunks (default 500 chars, 50 overlap) respecting word boundaries. |
| **Step 3** | Embed using `all-MiniLM-L6-v2` & store in ChromaDB | [`src/rag_pipeline/vector_store.py`](file:///C:/Users/Tulasi%20S/OneDrive/Desktop/rag/src/rag_pipeline/vector_store.py) | `ChromaVectorStore` generates dense 384-d embeddings and stores them in a local ChromaDB collection. |
| **Step 4** | User query input interface | [`src/cli.py`](file:///C:/Users/Tulasi%20S/OneDrive/Desktop/rag/src/cli.py) & [`src/app_streamlit.py`](file:///C:/Users/Tulasi%20S/OneDrive/Desktop/rag/src/app_streamlit.py) | Interactive CLI prompt loop and Streamlit web dashboard for uploading PDFs and entering queries. |
| **Step 5** | Embed query & extract top-k chunks from vector DB | [`src/rag_pipeline/vector_store.py`](file:///C:/Users/Tulasi%20S/OneDrive/Desktop/rag/src/rag_pipeline/vector_store.py) | Vector store computes query embeddings and retrieves nearest semantic chunks ranked by distance. |
| **Step 6** | Generate contextual response using modular LLM | [`src/rag_pipeline/generator.py`](file:///C:/Users/Tulasi%20S/OneDrive/Desktop/rag/src/rag_pipeline/generator.py) | `ModularGenerator` synthesizes answers using local extractive synthesis, Hugging Face, Gemini, or OpenAI. |

---

## 📁 Repository Structure

```
├── data/                       # Directory for input PDF documents
│   └── sample_rag_paper.pdf    # Auto-generated sample document
├── src/
│   ├── cli.py                  # Step 4: Interactive Command-Line Interface
│   ├── app_streamlit.py        # Step 4: Interactive Streamlit Web UI
│   ├── create_sample_pdf.py    # Helper utility to generate test PDFs
│   └── rag_pipeline/           # Core RAG modules
│       ├── __init__.py         # Package exports
│       ├── config.py           # Pipeline configuration dataclass
│       ├── pdf_reader.py       # Step 1: PDF ingestion & text extraction
│       ├── chunker.py          # Step 2: Sliding-window text chunking
│       ├── vector_store.py     # Steps 3 & 5: ChromaDB vector store & embeddings
│       ├── generator.py        # Step 6: Modular LLM response generator
│       └── pipeline.py         # End-to-end orchestrator
├── tests/                      # Automated test suite
│   ├── test_chunker.py
│   ├── test_vector_store.py
│   ├── test_generator.py
│   ├── test_pipeline.py
│   └── run_all_tests.py
├── architecture.json           # Architecture specification
├── api-contract.json           # API contract & schemas
├── ownership-map.json          # Engineering file ownership mapping
├── project-plan.json           # Project delivery plan & task tracking
├── milestones.json             # Milestone definitions & criteria
├── requirements.txt            # Python dependencies
├── run_cli.bat                 # Windows one-click CLI launcher
├── run_streamlit.bat           # Windows one-click Streamlit launcher
└── README.md
```

---

## 🛠️ Installation & Setup

1. **Clone or open the workspace:**
   ```bash
   cd "C:\Users\Tulasi S\OneDrive\Desktop\rag"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Configure environment variables:**
   Copy `.env.example` to `.env` if you want to use cloud LLM providers:
   ```bash
   cp .env.example .env
   ```
   *Note: If no API keys are provided, the pipeline automatically runs 100% offline using its built-in extractive synthesizer.*

---

## 🏃 Quick Start Guide

### 1. Generate a Sample PDF (for immediate testing)
```bash
python src/create_sample_pdf.py
```
This generates a test document at `data/sample_rag_paper.pdf`.

### 2. Run the Interactive CLI (Step 4)
You can run directly or use the Windows launcher `run_cli.bat`:
```bash
# Interactive mode (prompts for PDF path & questions)
python src/cli.py --interactive

# Or ingest and query in a single command:
python src/cli.py --pdf data/sample_rag_paper.pdf --query "What are the benefits of RAG?"
```

Sample CLI output:
```
==================================================
       Simple RAG Pipeline CLI
==================================================
Ingesting PDF: data/sample_rag_paper.pdf...
Success: Ingested 5 chunks.

Running query...

--- Answer ---
Based on the provided document:
- Reduced Hallucination: Grounding answers in retrieved factual documents drastically lowers false claims.
- Cost Efficiency: Updating domain knowledge requires simply updating the document collection or vector store...

--- Retrieved Context ---
[Chunk 1] 2. Benefits of RAG - Reduced Hallucination: Grounding answers in retrieved factual documents...
[Chunk 2] Step 3: Embedding and Vector Storage - Converting chunks into dense vector representations...
```

### 3. Run the Interactive Streamlit Chatbot Dashboard
```bash
streamlit run src/app_streamlit.py
```
*Or double click [`run_streamlit.bat`](file:///C:/Users/Tulasi%20S/OneDrive/Desktop/rag/run_streamlit.bat) on Windows.*

**Dashboard & Chatbot Features:**
- **🎙️ Built-in Voice Assistant**:
  - **🔊 Text-to-Speech (TTS)**: Click "Listen to Answer" to hear responses read aloud using natural browser speech synthesis, with adjustable speed, pitch, and an optional auto-speak mode.
  - **🎤 Speech-to-Text (STT)**: Dictate questions directly into the chatbot using your microphone with the "Speak Question" button.
- **✨ Clean Formatting with Emojis & Bullet Points**: Responses are structured with direct takeaway blockquotes (🎯), key points highlighted in bold with emojis (🔹, 🚀, 🛡️, ⚙️), and actionable summaries (💡).
- **💬 Conversational Chatbot**: Familiar ChatGPT-style interface with user/assistant avatars, streaming typewriter token generation, and persistent conversation history.
- **📚 Multi-Document Knowledge Hub**: Ingest multiple files simultaneously (`.pdf`, `.txt`, `.md`, `.csv`, `.docx`), paste raw text directly, or load the built-in sample paper with 1 click.
- **📊 Live System Metrics**: Real-time stats showing documents indexed, total vector chunks, active embedding model, and generator status.
- **🔍 Interactive Citations & Context Inspector**: Expandable source inspection cards beneath each response showing source document, page number, cosine distance, and exact excerpt.
- **💡 Suggested Question Pills**: 1-click prompt pills for instant summaries, benefits, step breakdowns, and fact-checking.
- **💾 Session Controls**: Clear chat history, reset vector database, or export entire conversations to Markdown.
- **⚙️ Backend Model Switcher**: Seamlessly switch between local offline synthesizer, Hugging Face, Gemini API, or OpenAI GPT.

---

## 🧪 Running Automated Tests

Run the full test suite using Python's built-in `unittest`:
```bash
python tests/run_all_tests.py
```
All unit tests and integration tests will execute, covering:
- PDF reading & text extraction
- Text chunking & overlap integrity
- ChromaDB vector store upsert & top-k retrieval
- Modular LLM prompt building & generator fallback
- End-to-end RAG pipeline ingest and query flow

---

## ⚙️ Modular Generation Providers

The `ModularGenerator` supports 4 backends:
1. **`fallback` (Default)**: Fast, zero-dependency local extractive synthesizer that matches query terms to the retrieved context. Requires no GPU, network, or external API keys.
2. **`huggingface`**: Uses local Hugging Face `transformers` pipeline (e.g. `google/flan-t5-base`).
3. **`gemini`**: Calls Google Gemini API when `GEMINI_API_KEY` is present.
4. **`openai`**: Calls OpenAI API when `OPENAI_API_KEY` is present.

---

## 📄 License
MIT License.
