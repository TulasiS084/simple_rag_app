"""
Utility script to generate a sample PDF document for testing the RAG pipeline.
Uses reportlab or fpdf if installed, or creates a standard minimalist PDF byte stream.
"""
import os

SAMPLE_TEXT = """
Artificial Intelligence and Retrieval-Augmented Generation (RAG)

1. Introduction to RAG
Retrieval-Augmented Generation (RAG) is an artificial intelligence framework that combines the strengths of traditional information retrieval systems (such as search engines or vector databases) with generative large language models (LLMs). Rather than relying solely on the static knowledge stored in an LLM's weights during pre-training, RAG dynamically retrieves relevant document snippets from external knowledge bases and feeds them as context into the prompt.

2. Benefits of RAG
- Reduced Hallucination: Grounding answers in retrieved factual documents drastically lowers false claims.
- Cost Efficiency: Updating domain knowledge requires simply updating the document collection or vector store, avoiding expensive fine-tuning or model retraining.
- Source Attribution: Users can inspect the exact source chunks and pages from which the answer was derived.
- Data Privacy: Proprietary or sensitive documents can be kept in a private local database like ChromaDB without uploading private datasets to external model trainers.

3. The RAG Pipeline Steps
Step 1: Document Ingestion - Extracting clean textual content from sources like PDF documents.
Step 2: Text Chunking - Splitting long documents into manageable, overlapping passages to preserve context.
Step 3: Embedding and Vector Storage - Converting chunks into dense vector representations using models such as sentence-transformers/all-MiniLM-L6-v2 and storing them in ChromaDB.
Step 4: User Query Interface - Accepting questions via Command Line Interface (CLI) or interactive web dashboards like Streamlit.
Step 5: Context Retrieval - Computing query embeddings and retrieving the top-k most relevant document chunks via cosine similarity.
Step 6: Contextual Generation - Synthesizing a grounded, accurate response using an LLM or extractive module.
"""

def generate_sample_pdf(output_path: str = "data/sample_rag_paper.pdf"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Try pypdf / reportlab or raw PDF construction
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        c = canvas.Canvas(output_path, pagesize=letter)
        y = 750
        for line in SAMPLE_TEXT.strip().split("\n"):
            if y < 60:
                c.showPage()
                y = 750
            if line.startswith("Artificial") or line.startswith("1.") or line.startswith("2.") or line.startswith("3."):
                c.setFont("Helvetica-Bold", 12)
            else:
                c.setFont("Helvetica", 10)
            c.drawString(50, y, line[:90])
            y -= 16
        c.save()
        print(f"Generated sample PDF using reportlab at: {output_path}")
        return output_path
    except ImportError:
        pass

    # Fallback: Minimalist valid raw PDF writer in pure Python (no external dependencies)
    content_stream = "BT /F1 10 Tf 50 750 Td ("
    escaped_text = SAMPLE_TEXT.replace("(", "\\(").replace(")", "\\)")
    lines = [l.strip() for l in escaped_text.split("\n") if l.strip()]
    pdf_ops = ["BT", "/F1 10 Tf", "50 750 Td"]
    for i, l in enumerate(lines):
        pdf_ops.append(f"({l[:80]}) Tj")
        pdf_ops.append("0 -16 Td")
    pdf_ops.append("ET")
    stream_content = "\n".join(pdf_ops)
    stream_len = len(stream_content.encode("latin1"))

    pdf_data = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {stream_len} >>
stream
{stream_content}
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000117 00000 n 
0000000227 00000 n 
0000000290 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
365
%%EOF
"""
    with open(output_path, "wb") as f:
        f.write(pdf_data.encode("latin1"))
    print(f"Generated minimal valid sample PDF at: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_sample_pdf()
