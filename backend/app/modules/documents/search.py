"""
Shared vector search utility.

Provides find_similar_chunks() which:
  - Generates an embedding for the query.
  - When running on PostgreSQL+pgvector: uses the <=> operator (native cosine distance).
  - When running on SQLite (dev fallback): loads chunks into memory and computes
    cosine distance with numpy/scipy.

This module replaces the inline scipy logic that was duplicated in rfi/service.py.
"""
import json
import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from app.modules.documents.models import DocumentChunk, Document
from app.shared.ai.embedding_client import get_embedding
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A chunk with its similarity score."""
    chunk: DocumentChunk
    distance: float       # Lower is more similar (cosine distance)
    document_id: str
    page_number: int | None
    section_heading: str | None


async def find_similar_chunks(
    db: AsyncSession,
    query: str,
    project_id: Optional[str] = None,
    top_k: int = 5,
) -> list[SearchResult]:
    """
    Find the most similar document chunks to a query string.
    
    Args:
        db: Async database session.
        query: The user's question or search text.
        project_id: Optional project scope (filters chunks to documents in this project).
        top_k: Number of results to return.
    
    Returns:
        List of SearchResult ordered by similarity (best first).
    """
    # 1. Generate embedding for the query
    try:
        query_embedding = get_embedding(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return []

    # 2. Decide search strategy based on database backend
    is_postgres = "postgresql" in settings.DATABASE_URL

    if is_postgres:
        return await _pgvector_search(db, query_embedding, project_id, top_k)
    else:
        return await _fallback_search(db, query_embedding, project_id, top_k)


async def _pgvector_search(
    db: AsyncSession,
    query_embedding: list[float],
    project_id: Optional[str],
    top_k: int,
) -> list[SearchResult]:
    """
    Use pgvector's cosine distance operator for fast vector search.
    Note: This requires the embedding column to be a pgvector Vector type.
    For the current TEXT-based storage, we fall through to _fallback_search.
    """
    # Since the current schema stores embeddings as JSON text (not pgvector Vector),
    # we use the fallback strategy even on Postgres. When the schema is migrated to
    # use a proper Vector column, this function can use the <=> operator directly.
    logger.info("pgvector search not yet available (embeddings stored as JSON text), using fallback")
    return await _fallback_search(db, query_embedding, project_id, top_k)


async def _fallback_search(
    db: AsyncSession,
    query_embedding: list[float],
    project_id: Optional[str],
    top_k: int,
) -> list[SearchResult]:
    """
    In-memory cosine distance computation.
    Loads all chunks (optionally scoped to a project), parses their JSON
    embeddings, computes distances, and returns the top-k results.
    """
    import numpy as np
    from scipy.spatial.distance import cosine

    # Build query with optional project_id filter
    if project_id:
        stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.project_id == project_id)
        )
    else:
        stmt = select(DocumentChunk)

    result = await db.execute(stmt)
    chunks = result.scalars().all()

    if not chunks:
        logger.info("No chunks found in database for similarity search")
        return []

    # Compute distances
    scored: list[tuple[float, DocumentChunk]] = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        try:
            emb = json.loads(chunk.embedding)
            if len(emb) != len(query_embedding):
                continue
            dist = cosine(emb, query_embedding)
            scored.append((dist, chunk))
        except (json.JSONDecodeError, ValueError):
            continue

    # Sort by distance (lower = more similar)
    scored.sort(key=lambda x: x[0])

    results: list[SearchResult] = []
    for dist, chunk in scored[:top_k]:
        results.append(SearchResult(
            chunk=chunk,
            distance=dist,
            document_id=chunk.document_id,
            page_number=chunk.page_number,
            section_heading=chunk.section_heading,
        ))

    logger.info(f"Vector search: {len(chunks)} chunks searched, {len(results)} results returned")
    return results
