import logging
from typing import Optional
from dataclasses import dataclass
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.shared.ai.embedding_client import get_embedding

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    chunk: dict
    distance: float
    document_id: str
    page_number: int | None
    section_heading: str | None


async def find_similar_chunks(
    db: AsyncIOMotorDatabase,
    query: str,
    project_id: Optional[str] = None,
    top_k: int = 5,
) -> list[SearchResult]:
    try:
        query_embedding = get_embedding(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return []

    # TODO: If using MongoDB Atlas Vector Search, you would use $vectorSearch here.
    # We will use the fallback in-memory scipy logic to ensure it works on local MongoDB as well.
    return await _fallback_search(db, query_embedding, project_id, top_k)


async def _fallback_search(
    db: AsyncIOMotorDatabase,
    query_embedding: list[float],
    project_id: Optional[str],
    top_k: int,
) -> list[SearchResult]:
    """In-memory cosine distance computation for MongoDB chunks without Atlas Vector Search index."""
    from scipy.spatial.distance import cosine

    # Build query
    query = {}
    if project_id:
        # Find document IDs in this project first
        project_docs = await db.documents.find({"project_id": project_id}, {"_id": 1}).to_list(None)
        doc_ids = [d["_id"] for d in project_docs]
        query["document_id"] = {"$in": doc_ids}

    # Fetch all chunks (this is inefficient for huge databases without Vector Search, but works for local Dev)
    chunks = await db.document_chunks.find(query).to_list(None)

    if not chunks:
        logger.info("No chunks found in database for similarity search")
        return []

    scored = []
    for chunk in chunks:
        emb = chunk.get("embedding")
        if not emb or len(emb) != len(query_embedding):
            continue
        try:
            dist = cosine(emb, query_embedding)
            scored.append((dist, chunk))
        except ValueError:
            continue

    scored.sort(key=lambda x: x[0])

    results = []
    for dist, chunk in scored[:top_k]:
        chunk["id"] = chunk.pop("_id")
        results.append(SearchResult(
            chunk=chunk,
            distance=dist,
            document_id=chunk["document_id"],
            page_number=chunk.get("page_number"),
            section_heading=chunk.get("section_heading"),
        ))

    logger.info(f"Vector search: {len(chunks)} chunks searched, {len(results)} results returned")
    return results
