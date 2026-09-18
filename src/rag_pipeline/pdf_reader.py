import os
import re
from typing import List, Dict, Optional


def clean_pdf_text(text: str) -> str:
    """
    Clean extracted text while preserving line breaks and paragraph structure.
    Normalizes carriage returns, cleans tabs and excessive horizontal spaces
    per line, and collapses 3 or more consecutive newlines into paragraph breaks (\n\n).
    """
    if not text:
        return ""
    # Normalize carriage returns
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    # Clean tabs and excessive horizontal spaces per line, trimming leading/trailing spaces
    cleaned_lines = [re.sub(r'[ \t\f\v]+', ' ', line).strip() for line in normalized.split("\n")]
    # Rejoin lines with newline
    joined = "\n".join(cleaned_lines)
    # Collapse 3 or more consecutive newlines into paragraph breaks (\n\n)
    cleaned = re.sub(r'\n{3,}', '\n\n', joined)
    return cleaned.strip()


def extract_text_from_pdf(pdf_path: str, original_filename: Optional[str] = None) -> List[Dict]:
    """
    Extract text page-by-page from a PDF file.

    Args:
        pdf_path: Path to the PDF file.
        original_filename: Optional actual filename to be recorded in metadata.

    Returns:
        List of dictionaries containing page text, raw text, word count,
        character count, and metadata.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
    
    filename = original_filename or os.path.basename(pdf_path)
    extracted_pages = []
    
    # Try pypdf first, then PyPDF2 fallback
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader

        reader = PdfReader(pdf_path)

        # Check if PDF is encrypted or password-protected
        if getattr(reader, "is_encrypted", False):
            try:
                decrypted = reader.decrypt("")
                if decrypted == 0:
                    raise ValueError(
                        f"No extractable text found in '{filename}'. "
                        "This PDF may be a scanned image without an OCR layer or encrypted. "
                        "Please provide a document with selectable text."
                    )
            except Exception:
                raise ValueError(
                    f"No extractable text found in '{filename}'. "
                    "This PDF may be a scanned image without an OCR layer or encrypted. "
                    "Please provide a document with selectable text."
                )

        for page_num, page in enumerate(reader.pages):
            raw_text = page.extract_text() or ""
            cleaned_text = clean_pdf_text(raw_text)
            if cleaned_text:
                word_count = len(cleaned_text.split())
                char_count = len(cleaned_text)
                extracted_pages.append({
                    "text": cleaned_text,
                    "raw_text": raw_text,
                    "word_count": word_count,
                    "char_count": char_count,
                    "character_count": char_count,
                    "words": word_count,
                    "chars": char_count,
                    "metadata": {
                        "source": filename,
                        "page": page_num + 1,
                        "type": "pdf",
                        "word_count": word_count,
                        "char_count": char_count,
                        "raw_text": raw_text
                    }
                })
    except (ValueError, FileNotFoundError):
        raise
    except Exception as e:
        err_msg = str(e).lower()
        if "encrypt" in err_msg or "password" in err_msg:
            raise ValueError(
                f"No extractable text found in '{filename}'. "
                "This PDF may be a scanned image without an OCR layer or encrypted. "
                "Please provide a document with selectable text."
            )
        raise RuntimeError(f"Failed to read PDF file {pdf_path}: {e}")

    total_chars = sum(p["char_count"] for p in extracted_pages)
    if not extracted_pages or total_chars == 0:
        raise ValueError(
            f"No extractable text found in '{filename}'. "
            "This PDF may be a scanned image without an OCR layer or encrypted. "
            "Please provide a document with selectable text."
        )

    return extracted_pages


def extract_text_from_document(file_path: str, original_filename: Optional[str] = None) -> List[Dict]:
    """
    Universal document text extractor supporting PDF, TXT, Markdown, CSV, and code files.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at: {file_path}")

    ext = os.path.splitext(original_filename or file_path)[1].lower()
    filename = original_filename or os.path.basename(file_path)

    if ext == ".pdf":
        return extract_text_from_pdf(file_path, original_filename=filename)
    
    elif ext in [".txt", ".md", ".markdown", ".csv", ".json", ".log", ".py", ".html"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise RuntimeError(f"Error reading text document {filename}: {e}")

        cleaned_text = clean_pdf_text(content)
        if not cleaned_text:
            return []

        word_count = len(cleaned_text.split())
        char_count = len(cleaned_text)
        return [{
            "text": cleaned_text,
            "raw_text": content,
            "word_count": word_count,
            "char_count": char_count,
            "character_count": char_count,
            "words": word_count,
            "chars": char_count,
            "metadata": {
                "source": filename,
                "page": 1,
                "type": ext.lstrip("."),
                "word_count": word_count,
                "char_count": char_count,
                "raw_text": content
            }
        }]

    elif ext in [".docx", ".doc"]:
        try:
            import docx
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                p_text = re.sub(r'[ \t\f\v]+', ' ', para.text).strip()
                if p_text:
                    full_text.append(p_text)
            cleaned = "\n\n".join(full_text)
            if not cleaned:
                return []
            word_count = len(cleaned.split())
            char_count = len(cleaned)
            return [{
                "text": cleaned,
                "raw_text": cleaned,
                "word_count": word_count,
                "char_count": char_count,
                "character_count": char_count,
                "words": word_count,
                "chars": char_count,
                "metadata": {
                    "source": filename,
                    "page": 1,
                    "type": "docx",
                    "word_count": word_count,
                    "char_count": char_count,
                    "raw_text": cleaned
                }
            }]
        except ImportError:
            # Fallback basic binary string extraction for docx
            with open(file_path, "rb") as f:
                raw_bytes = f.read()
            text = "".join(chr(b) for b in raw_bytes if 32 <= b <= 126 or b in (10, 13))
            cleaned = clean_pdf_text(text)
            if not cleaned:
                return []
            word_count = len(cleaned.split())
            char_count = len(cleaned)
            return [{
                "text": cleaned,
                "raw_text": text,
                "word_count": word_count,
                "char_count": char_count,
                "character_count": char_count,
                "words": word_count,
                "chars": char_count,
                "metadata": {
                    "source": filename,
                    "page": 1,
                    "type": "docx-raw",
                    "word_count": word_count,
                    "char_count": char_count,
                    "raw_text": text
                }
            }]
    else:
        # Generic text attempt
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            cleaned = clean_pdf_text(content)
            if not cleaned:
                return []
            word_count = len(cleaned.split())
            char_count = len(cleaned)
            return [{
                "text": cleaned,
                "raw_text": content,
                "word_count": word_count,
                "char_count": char_count,
                "character_count": char_count,
                "words": word_count,
                "chars": char_count,
                "metadata": {
                    "source": filename,
                    "page": 1,
                    "type": "generic",
                    "word_count": word_count,
                    "char_count": char_count,
                    "raw_text": content
                }
            }]
        except Exception as e:
            raise ValueError(f"Unsupported file extension '{ext}' for file {filename}: {e}")


class DocumentReader:
    """Universal Document Reader for RAG pipeline."""

    def __init__(self, file_path: Optional[str] = None, original_filename: Optional[str] = None):
        self.file_path = file_path
        self.original_filename = original_filename

    def read(self, file_path: Optional[str] = None, original_filename: Optional[str] = None) -> List[Dict]:
        path = file_path or self.file_path
        orig = original_filename or self.original_filename
        if not path:
            raise ValueError("No file path specified")
        return extract_text_from_document(path, original_filename=orig)


class PDFReader(DocumentReader):
    """PDFReader class wrapper for backward compatibility."""

    def read(self, pdf_path: Optional[str] = None, original_filename: Optional[str] = None) -> List[Dict]:
        path = pdf_path or self.file_path
        orig = original_filename or self.original_filename
        if not path:
            raise ValueError("No PDF path specified")
        return extract_text_from_pdf(path, original_filename=orig)

