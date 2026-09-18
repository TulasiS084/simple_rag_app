import os
import re
from typing import List, Dict, Optional

def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract text page-by-page from a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of dictionaries containing page text and metadata.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
    
    if not pdf_path.lower().endswith(".pdf"):
        raise ValueError("File must have a .pdf extension")

    extracted_pages = []
    
    # Try pypdf first, then PyPDF2 fallback
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader

        reader = PdfReader(pdf_path)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                # Clean whitespace
                cleaned_text = re.sub(r'\s+', ' ', text).strip()
                if cleaned_text:
                    extracted_pages.append({
                        "text": cleaned_text,
                        "metadata": {
                            "source": os.path.basename(pdf_path),
                            "page": page_num + 1,
                            "type": "pdf"
                        }
                    })
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF file {pdf_path}: {e}")

    return extracted_pages


def extract_text_from_document(file_path: str) -> List[Dict]:
    """
    Universal document text extractor supporting PDF, TXT, Markdown, CSV, and code files.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    
    elif ext in [".txt", ".md", ".markdown", ".csv", ".json", ".log", ".py", ".html"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise RuntimeError(f"Error reading text document {filename}: {e}")

        # Clean content
        cleaned_text = re.sub(r'[ \t]+', ' ', content).strip()
        if not cleaned_text:
            return []

        # Split long documents into logical sections/pages (e.g. every 1500 chars) if needed
        return [{
            "text": cleaned_text,
            "metadata": {
                "source": filename,
                "page": 1,
                "type": ext.lstrip(".")
            }
        }]

    elif ext in [".docx", ".doc"]:
        try:
            import docx
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            cleaned = "\n".join(full_text)
            return [{
                "text": cleaned,
                "metadata": {
                    "source": filename,
                    "page": 1,
                    "type": "docx"
                }
            }]
        except ImportError:
            # Fallback basic binary string extraction for docx
            with open(file_path, "rb") as f:
                raw_bytes = f.read()
            text = "".join(chr(b) for b in raw_bytes if 32 <= b <= 126 or b in (10, 13))
            cleaned = re.sub(r'\s+', ' ', text).strip()
            return [{
                "text": cleaned,
                "metadata": {
                    "source": filename,
                    "page": 1,
                    "type": "docx-raw"
                }
            }]
    else:
        # Generic text attempt
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return [{
                "text": re.sub(r'\s+', ' ', content).strip(),
                "metadata": {
                    "source": filename,
                    "page": 1,
                    "type": "generic"
                }
            }]
        except Exception as e:
            raise ValueError(f"Unsupported file extension '{ext}' for file {filename}: {e}")


class DocumentReader:
    """Universal Document Reader for RAG pipeline."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def read(self, file_path: Optional[str] = None) -> List[Dict]:
        path = file_path or self.file_path
        if not path:
            raise ValueError("No file path specified")
        return extract_text_from_document(path)


class PDFReader(DocumentReader):
    """PDFReader class wrapper for backward compatibility."""

    def read(self, pdf_path: Optional[str] = None) -> List[Dict]:
        path = pdf_path or self.file_path
        if not path:
            raise ValueError("No PDF path specified")
        return extract_text_from_document(path)
