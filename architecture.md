# Simple RAG Pipeline Architecture

## System Overview
The Simple RAG Pipeline is a local Python-based application that allows users to ingest PDF documents, process them into vectorized chunks, and query them using Large Language Models (LLMs). It provides both an interactive Command Line Interface (CLI) and a Streamlit Web UI.

## Technology Stack
- **Backend**: Python 3.10+
- **Embedding Models**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector Database**: ChromaDB
- **LLM Generators**: HuggingFace local models, Gemini/OpenAI (via API), local template fallback
- **Frontend/UI**: Streamlit, argparse/click (CLI)

## Service Boundaries
1. **Data Ingestion (`data-lead`)**: Reads PDFs, extracts text, converts text to chunks (with configurable overlap/size), and embeds/stores them in ChromaDB.
2. **Pipeline & Generation (`backend-lead`)**: Orchestrates the RAG flow, retrieves context chunks from ChromaDB, and generates LLM responses based on context.
3. **User Interface (`frontend-lead`)**: Exposes the pipeline functionality to users via Streamlit and CLI.

## Key Architectural Decisions
1. **Modular LLM Generator**: The generator supports multiple backends (local transformers, external APIs, offline fallback) to allow flexible deployment without strict dependency on high-end GPUs or paid APIs.
2. **Local Vector Database**: ChromaDB is used as it can run entirely locally without requiring a separate server setup, aligning with the offline capabilities of the app.
3. **Clear Ownership**: The directory tree is strictly partitioned between data, backend, frontend, qa, and devops to allow parallel workstreams without Git conflicts.
