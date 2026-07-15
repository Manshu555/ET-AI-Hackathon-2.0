"""
RFI / Knowledge Chat service.

Handles RAG-based question answering over the project document corpus.
Uses the shared vector search utility from documents/search.py instead
of inline scipy logic.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.modules.rfi.models import ChatSession, ChatMessage
from app.modules.documents.search import find_similar_chunks
from app.core.config import settings
import json
import logging
import re

logger = logging.getLogger(__name__)


def _retrieval_fallback(user_message: str, results) -> str:
    """Return a helpful response when the hosted LLM is unavailable."""
    normalized_message = user_message.strip().lower()
    if (
        re.fullmatch(r"(?:hi|hii+|hello|hey|good (?:morning|afternoon|evening))(?:[!.?\s]*)", normalized_message)
        or re.search(r"\bhow (?:can|do) (?:you|u) assist\b", normalized_message)
    ):
        return (
            "Hello! I can help you find requirements in the current project's "
            "specifications and submittals. Ask about equipment capacity, clearances, "
            "temperatures, schedules, or vendor submissions."
        )

    if not results:
        return (
            "The AI service is temporarily unavailable, and I could not find "
            "a relevant passage in the uploaded project documents. Please try again later."
        )

    excerpts = []
    for result in results[:2]:
        location = f"Page {result.page_number}" if result.page_number else "Document excerpt"
        if result.section_heading:
            location += f", {result.section_heading}"
        excerpts.append(f"- {result.chunk.chunk_text.strip()}  — *{location}*")

    return (
        "The AI service is temporarily unavailable, but I found these relevant "
        "project-document excerpts:\n\n"
        + "\n".join(excerpts)
    )


async def process_chat_message(db: AsyncSession, session_id: str, user_message: str, project_id: str, user_id: str) -> str:
    context_str = ""
    citations = []
    results = []

    # --- 1. RAG retrieval using shared vector search ---
    try:
        results = await find_similar_chunks(
            db=db,
            query=user_message,
            project_id=project_id,
            top_k=5,
        )

        if results:
            context_texts = []
            for result in results:
                chunk = result.chunk
                source_label = f"[Page {result.page_number}]" if result.page_number else f"[{chunk.id}]"
                if result.section_heading:
                    source_label += f" ({result.section_heading})"
                context_texts.append(f"Source {source_label}: {chunk.chunk_text}")
                citations.append({
                    "chunk_id": chunk.id,
                    "document_id": result.document_id,
                    "page_number": result.page_number,
                    "section": result.section_heading,
                })

            context_str = "\n\n".join(context_texts)
    except Exception as e:
        logger.warning(f"RAG retrieval error (running in fallback mode): {e}")
        context_str = ""

    # --- 2. Call Gemini LLM ---
    if not settings.GEMINI_API_KEY:
        ai_reply = "The Gemini API key is not configured. Please set GEMINI_API_KEY in the backend .env file."
    else:
        try:
            from google import genai

            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            if context_str:
                prompt = f"""You are a construction engineering assistant answering an RFI (Request for Information).
Use the following context from project documents to answer the question. Cite your sources using the page numbers and section headings provided.
If you cannot find the answer in the provided context, say so honestly — do not guess.

Context:
{context_str}

Question: {user_message}"""
            else:
                prompt = f"""You are a construction engineering assistant for the EPC-Intel platform.
Answer the following question from your general knowledge of construction engineering, specifications, and submittals.
Be helpful and professional.

Question: {user_message}"""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            ai_reply = response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            ai_reply = _retrieval_fallback(user_message, results)

    # --- 3. Persist messages to DB (non-fatal if DB has issues) ---
    try:
        session_result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        chat_session = session_result.scalars().first()
        if chat_session is None:
            chat_session = ChatSession(id=session_id, project_id=project_id, user_id=user_id)
            db.add(chat_session)
        elif chat_session.project_id != project_id or chat_session.user_id != user_id:
            raise ValueError("Chat session does not belong to the current user and project")
        user_msg = ChatMessage(session_id=session_id, role="user", content=user_message)
        ai_msg = ChatMessage(
            session_id=session_id,
            role="ai",
            content=ai_reply,
            citations=json.dumps(citations) if citations else None
        )
        db.add(user_msg)
        db.add(ai_msg)
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to persist chat messages to DB (non-fatal): {e}")
        await db.rollback()

    return ai_reply
