"""Extracts text from PDF files into a PDFDocument struct."""
import re
from pathlib import Path
import fitz
from redactor.models import PDFDocument, PDFPage


def extract(pdf_path: str) -> PDFDocument:
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text:
            pages.append(PDFPage(page_num=i, text=_normalize(text)))
    return PDFDocument(filename=Path(pdf_path).name, pages=pages)


def _normalize(text: str) -> str:
    # Rejoin tokens split across lines by a hyphen (e.g. "646-237-\n8585")
    text = re.sub(r"(\S)-\n(\S)", r"\1-\2", text)
    # Collapse remaining single newlines to spaces (PDF layout artifact)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # Collapse runs of spaces
    text = re.sub(r" {2,}", " ", text)
    return text
