"""
PDF text extraction with per-page metadata.

Uses PyMuPDF (fitz) to extract text from each page, tracking page numbers
and detecting section headings. A failed page produces a warning rather
than aborting the entire document.
"""
import tempfile
import os
import re
import logging
from dataclasses import dataclass, field

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class ParsedPage:
    """Represents a single extracted page from a PDF."""
    page_number: int          # 1-indexed
    text: str                 # Raw extracted text
    headings: list[str] = field(default_factory=list)  # Detected section headings


@dataclass
class ParsedDocument:
    """Result of parsing an entire PDF."""
    pages: list[ParsedPage]
    page_count: int
    failed_pages: list[int]   # Pages where extraction failed


# Patterns that look like section headings in engineering docs
_HEADING_PATTERNS = [
    re.compile(r"^(\d+\.[\d.]*)\s+(.+)$"),          # "4.2.1 Cooling Requirements"
    re.compile(r"^(Section\s+\d+[.\d]*)\s*[:\-–]\s*(.+)$", re.IGNORECASE),
    re.compile(r"^(PART\s+\d+)\s*[:\-–]\s*(.+)$", re.IGNORECASE),
    re.compile(r"^(Article\s+\d+[.\d]*)\s*[:\-–]\s*(.+)$", re.IGNORECASE),
]


def _detect_headings(text: str) -> list[str]:
    """Extract likely section headings from a page's text."""
    headings = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) > 200:
            continue

        # Check numbered section patterns
        for pattern in _HEADING_PATTERNS:
            match = pattern.match(line)
            if match:
                headings.append(line)
                break
        else:
            # ALL-CAPS lines that are short enough to be headings (5-80 chars)
            if line.isupper() and 5 <= len(line) <= 80 and not line.startswith(("•", "-", "*")):
                headings.append(line)

    return headings


def parse_pdf_bytes(content: bytes) -> ParsedDocument:
    """
    Parse a PDF from raw bytes and return structured page data.
    
    Args:
        content: Raw PDF file bytes.
    
    Returns:
        ParsedDocument with per-page text, headings, and metadata.
    """
    pages: list[ParsedPage] = []
    failed_pages: list[int] = []

    # Write to temp file for PyMuPDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        pdf = fitz.open(tmp_path)
        page_count = len(pdf)

        for page_idx in range(page_count):
            page_num = page_idx + 1  # 1-indexed
            try:
                page = pdf[page_idx]
                text = page.get_text("text")

                # If extraction produced mostly garbage, flag it
                if not text or len(text.strip()) < 10:
                    logger.warning(f"Page {page_num}: Very little text extracted (OCR may be needed)")
                    failed_pages.append(page_num)
                    # Still create a page entry with whatever we got
                    pages.append(ParsedPage(
                        page_number=page_num,
                        text=text.strip() if text else "",
                        headings=[],
                    ))
                    continue

                headings = _detect_headings(text)
                pages.append(ParsedPage(
                    page_number=page_num,
                    text=text,
                    headings=headings,
                ))
            except Exception as e:
                logger.error(f"Page {page_num}: Extraction failed — {e}")
                failed_pages.append(page_num)

        pdf.close()
    finally:
        os.unlink(tmp_path)

    return ParsedDocument(
        pages=pages,
        page_count=page_count if 'page_count' in dir() else len(pages),
        failed_pages=failed_pages,
    )
