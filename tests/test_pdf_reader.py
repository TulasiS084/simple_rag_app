import unittest
import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.rag_pipeline.pdf_reader import (
        extract_text_from_pdf,
        extract_text_from_document,
        clean_pdf_text,
        PDFReader,
        DocumentReader
    )
    from src.create_sample_pdf import generate_sample_pdf
except ImportError:
    from rag_pipeline.pdf_reader import (
        extract_text_from_pdf,
        extract_text_from_document,
        clean_pdf_text,
        PDFReader,
        DocumentReader
    )
    from create_sample_pdf import generate_sample_pdf


def create_blank_pdf(path: str):
    """Generate a valid minimal PDF with no extractable text."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000060 00000 n \n"
        b"0000000117 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
        b"startxref\n190\n%%EOF\n"
    )
    with open(path, "wb") as f:
        f.write(pdf_content)


class TestPDFReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.valid_pdf = os.path.join(cls.temp_dir.name, "sample.pdf")
        generate_sample_pdf(cls.valid_pdf)

        cls.blank_pdf = os.path.join(cls.temp_dir.name, "blank.pdf")
        create_blank_pdf(cls.blank_pdf)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_clean_pdf_text_preserves_breaks_and_cleans_whitespace(self):
        # Paragraphs and lines
        raw = "Line 1 of para 1\t\t \nLine 2 of para 1   \n\nLine 1 of para 2\n\n\n\nLine 1 of para 3"
        cleaned = clean_pdf_text(raw)

        # Single line breaks preserved
        self.assertIn("Line 1 of para 1\nLine 2 of para 1", cleaned)
        # Paragraph breaks (\n\n) preserved
        self.assertIn("Line 2 of para 1\n\nLine 1 of para 2", cleaned)
        # Excessive newlines collapsed to \n\n
        self.assertIn("Line 1 of para 2\n\nLine 1 of para 3", cleaned)
        # Tabs and multiple spaces cleaned per line
        self.assertNotIn("\t", cleaned)
        self.assertNotIn("   ", cleaned)

    def test_clean_pdf_text_empty_input(self):
        self.assertEqual(clean_pdf_text(""), "")
        self.assertEqual(clean_pdf_text("   \n \t  \n  "), "")

    def test_extract_text_from_valid_pdf(self):
        sections = extract_text_from_pdf(self.valid_pdf)
        self.assertGreater(len(sections), 0)

        for sec in sections:
            self.assertIn("text", sec)
            self.assertIn("raw_text", sec)
            self.assertIn("word_count", sec)
            self.assertIn("char_count", sec)
            self.assertIn("words", sec)
            self.assertIn("chars", sec)
            self.assertGreater(sec["char_count"], 0)
            self.assertGreater(sec["word_count"], 0)
            self.assertEqual(sec["char_count"], len(sec["text"]))
            self.assertEqual(sec["word_count"], len(sec["text"].split()))
            self.assertIn("source", sec["metadata"])
            self.assertIn("page", sec["metadata"])
            self.assertEqual(sec["metadata"]["type"], "pdf")

    def test_extract_text_from_blank_pdf_raises_value_error(self):
        filename = os.path.basename(self.blank_pdf)
        expected_msg = (
            f"No extractable text found in '{filename}'. "
            "This PDF may be a scanned image without an OCR layer or encrypted. "
            "Please provide a document with selectable text."
        )
        with self.assertRaises(ValueError) as ctx:
            extract_text_from_pdf(self.blank_pdf)
        self.assertEqual(str(ctx.exception), expected_msg)

    def test_extract_text_non_pdf_extension_raises_value_error(self):
        txt_path = os.path.join(self.temp_dir.name, "doc.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Some text")
        with self.assertRaises(ValueError):
            extract_text_from_pdf(txt_path)

    def test_extract_text_non_existent_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            extract_text_from_pdf("non_existent_file.pdf")

    def test_extract_text_from_document_text_file(self):
        txt_path = os.path.join(self.temp_dir.name, "sample.txt")
        sample_body = "Paragraph 1 line 1\nParagraph 1 line 2\n\nParagraph 2 line 1"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(sample_body)

        sections = extract_text_from_document(txt_path)
        self.assertEqual(len(sections), 1)
        sec = sections[0]
        self.assertIn("text", sec)
        self.assertIn("raw_text", sec)
        self.assertIn("word_count", sec)
        self.assertIn("char_count", sec)
        self.assertIn("\n\n", sec["text"])
        self.assertEqual(sec["char_count"], len(sec["text"]))
        self.assertEqual(sec["word_count"], len(sec["text"].split()))

    def test_pdf_reader_and_document_reader_classes(self):
        pdf_reader = PDFReader()
        sections = pdf_reader.read(self.valid_pdf)
        self.assertGreater(len(sections), 0)

        doc_reader = DocumentReader(self.valid_pdf)
        sections2 = doc_reader.read()
        self.assertGreater(len(sections2), 0)

        with self.assertRaises(ValueError):
            PDFReader().read(None)

        with self.assertRaises(ValueError):
            DocumentReader().read(None)


if __name__ == "__main__":
    unittest.main()
