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

logger = logging.getLogger(__name__)


async def process_chat_message(db: AsyncSession, session_id: str, user_message: str) -> str:
    context_str = ""
    citations = []

    # --- 1. RAG retrieval using shared vector search ---
    try:
        results = await find_similar_chunks(
            db=db,
            query=user_message,
            project_id=None,  # Search across all projects for now
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
            ai_reply = f"I'm sorry, I encountered an error communicating with the AI service: {str(e)}"

    # --- 3. Persist messages to DB (non-fatal if DB has issues) ---
    try:
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

    return ai_reply
