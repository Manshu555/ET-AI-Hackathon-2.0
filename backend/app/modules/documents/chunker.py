"""
Page-aware, section-detecting document chunker.

Creates ~500-token chunks with 100-token overlap. Never splits across page
boundaries where possible. Each chunk carries its source page number and
the most recent section heading for context.
"""
import logging
from dataclasses import dataclass

from app.modules.documents.parser import ParsedPage

logger = logging.getLogger(__name__)

# Approximate tokens as words (good enough for hackathon; real tokenizer optional)
CHUNK_SIZE = 500       # target words per chunk
CHUNK_OVERLAP = 100    # overlap words between consecutive chunks


@dataclass
class Chunk:
    """A single text chunk with provenance metadata."""
    text: str
    page_number: int          # Source page (1-indexed)
    section_heading: str | None  # Last detected section heading


def _chunk_page_text(
    text: str,
    page_number: int,
    headings: list[str],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    Split a single page's text into overlapping word-level chunks.
    
    Each chunk is tagged with its page number and the most recent heading
    that appeared before the chunk started.
    """
    words = text.split()
    if not words:
        return []

    # Build a mapping: word_index → most recent heading up to that point
    # We locate headings in the text by matching heading strings
    current_heading: str | None = None
    heading_at_word: dict[int, str] = {}

    running_text = ""
    word_idx = 0
    for heading in headings:
        # Find where in the word list this heading appears
        heading_words = heading.split()
        heading_len = len(heading_words)
        for i in range(word_idx, max(0, len(words) - heading_len + 1)):
            if words[i:i + heading_len] == heading_words:
                heading_at_word[i] = heading
                word_idx = i + heading_len
                break

    # Now chunk with overlap
    chunks: list[Chunk] = []
    i = 0
    while i < len(words):
        end = min(i + chunk_size, len(words))
        chunk_words = words[i:end]
        chunk_text = " ".join(chunk_words)

        # Find the most recent heading for this chunk
        for hi in sorted(heading_at_word.keys(), reverse=True):
            if hi <= i:
                current_heading = heading_at_word[hi]
                break

        if chunk_text.strip():
            chunks.append(Chunk(
                text=chunk_text,
                page_number=page_number,
                section_heading=current_heading,
            ))

        # Advance with overlap
        i += chunk_size - overlap
        if i >= len(words):
            break
        # Don't create tiny trailing chunks
        if len(words) - i < overlap:
            break

    return chunks


def chunk_pages(
    pages: list[ParsedPage],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    Chunk an entire parsed document, respecting page boundaries.
    
    Each page is chunked independently so that chunks never span
    across page boundaries. This preserves accurate page_number metadata
    for citation purposes.
    
    Args:
        pages: List of ParsedPage objects from the parser.
        chunk_size: Target number of words per chunk.
        overlap: Number of overlapping words between consecutive chunks.
    
    Returns:
        Ordered list of Chunks with page and section metadata.
    """
    all_chunks: list[Chunk] = []

    for page in pages:
        if not page.text or not page.text.strip():
            continue

        page_chunks = _chunk_page_text(
            text=page.text,
            page_number=page.page_number,
            headings=page.headings,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        all_chunks.extend(page_chunks)

    logger.info(f"Created {len(all_chunks)} chunks from {len(pages)} pages")
    return all_chunks
