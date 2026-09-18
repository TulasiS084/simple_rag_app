import argparse
import sys
import os

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.rag_pipeline import RAGPipeline
except ImportError:
    from rag_pipeline import RAGPipeline

def main():
    parser = argparse.ArgumentParser(description="Simple RAG Pipeline CLI",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
Examples:
  # Ingest a PDF
  python src/cli.py --pdf data/sample.pdf

  # Query non-interactively
  python src/cli.py --query "What is this document about?"

  # Interactive mode
  python src/cli.py --interactive
""")
    parser.add_argument("--pdf", type=str, help="Path to PDF file to ingest")
    parser.add_argument("--query", type=str, help="Query to ask the RAG pipeline")
    parser.add_argument("--top-k", type=int, default=4, help="Number of chunks to retrieve")
    parser.add_argument("--interactive", action="store_true", help="Start interactive query loop")
    parser.add_argument("--generator", type=str, choices=["local", "gemini", "openai", "fallback"], default="local", help="Generator model type")
    
    args = parser.parse_args()
    
    try:
        pipeline = RAGPipeline()
    except Exception as e:
        print(f"\033[91mError initializing pipeline: {e}\033[0m")
        sys.exit(1)
    
    print("\033[96m" + "="*50 + "\033[0m")
    print("\033[96m       Simple RAG Pipeline CLI\033[0m")
    print("\033[96m" + "="*50 + "\033[0m")
    
    if args.pdf:
        print(f"\033[93mIngesting PDF: {args.pdf}...\033[0m")
        try:
            status = pipeline.ingest(file_path=args.pdf, chunk_size=1000, chunk_overlap=150)
            print(f"\033[92mSuccess: Ingested {status.get('chunks_processed', 0)} chunks.\033[0m")
        except Exception as e:
            print(f"\033[91mError ingesting PDF: {e}\033[0m")
            
    if args.query and not args.interactive:
        _run_query(pipeline, args.query, args.top_k, args.generator)
        
    if args.interactive:
        if not args.pdf and pipeline.vector_store.count() == 0:
            default_pdf = os.path.join("data", "sample_rag_paper.pdf")
            prompt_msg = f"\033[93mNo document currently indexed. Enter PDF path (or press Enter for '{default_pdf}'): \033[0m"
            try:
                pdf_input = input(prompt_msg).strip()
                pdf_to_ingest = pdf_input or default_pdf
                if os.path.exists(pdf_to_ingest):
                    print(f"\033[93mIngesting PDF: {pdf_to_ingest}...\033[0m")
                    status = pipeline.ingest(file_path=pdf_to_ingest, chunk_size=1000, chunk_overlap=150)
                    print(f"\033[92mSuccess: Ingested {status.get('chunks_processed', 0)} chunks.\033[0m")
                else:
                    print(f"\033[91mWarning: File not found at '{pdf_to_ingest}'. You can ingest later using --pdf.\033[0m")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                return

        print("\033[92mEntering interactive mode. Type 'exit' or 'quit' to stop.\033[0m")
        while True:
            try:
                user_input = input("\033[95mQuestion: \033[0m").strip()
                if user_input.lower() in ['exit', 'quit']:
                    print("Exiting...")
                    break
                if user_input:
                    _run_query(pipeline, user_input, args.top_k, args.generator)
            except KeyboardInterrupt:
                print("\nExiting...")
                break

def _run_query(pipeline, query, top_k, generator):
    print(f"\n\033[94mRunning query...\033[0m")
    try:
        result = pipeline.query(query=query, top_k=top_k, model_type=generator)
        response_text = result.get("response", "No response.")
        context = result.get("context_chunks", [])
        
        print("\n\033[92m" + "="*50)
        print("                 🎯 AI Response")
        print("="*50 + "\033[0m\n")
        print(response_text)
        print("\n\033[93m" + "-"*50)
        print("             📑 Retrieved Context Chunks")
        print("-"*50 + "\033[0m")
        for i, chunk in enumerate(context, 1):
            if isinstance(chunk, dict):
                text = chunk.get("text", "")
                score = chunk.get("score")
                meta = chunk.get("metadata", {})
                source = meta.get("source", "Document")
                page = meta.get("page", 1)
                score_str = f"Distance: {score:.4f}" if score is not None else "Matched"
                print(f"\033[96m📌 [Chunk {i}] • {source} (Page {page}) • {score_str}\033[0m")
                print(f"\033[90m{text}\033[0m\n")
            else:
                print(f"\033[96m📌 [Chunk {i}]\033[0m\n\033[90m{chunk}\033[0m\n")
    except Exception as e:
        print(f"\033[91mError during query: {e}\033[0m")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # If no arguments are passed, assume interactive mode by default
        sys.argv.append("--interactive")
    main()
