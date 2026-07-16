import os
import json
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.documents.search import find_similar_chunks
import uuid
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


async def process_chat_message(db: AsyncIOMotorDatabase, session_id: str, message: str) -> str:
    from openai import OpenAI
    
    session = await db.chat_sessions.find_one({"_id": session_id})
    if not session:
        return "Session not found."

    # 1. RAG Retrieval - Find similar chunks
    search_results = await find_similar_chunks(db, message, project_id=session.get("project_id"), top_k=5)

    context_texts = []
    citations = []
    for sr in search_results:
        # Resolve document filename
        doc = await db.documents.find_one({"_id": sr.document_id})
        filename = doc["filename"] if doc else "Unknown Document"
        
        ctx = f"Document: {filename}\nPage: {sr.page_number or 'N/A'}\nSection: {sr.section_heading or 'N/A'}\nText: {sr.chunk['chunk_text']}"
        context_texts.append(ctx)
        citations.append(sr.chunk["id"])

    context_block = "\n\n---\n\n".join(context_texts) if context_texts else "No specific documents found."

    # 2. OpenRouter API Call
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set in environment.")
        return "I'm sorry, the AI service is currently unconfigured (Missing OpenRouter API Key)."
        
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        prompt = f"""You are a helpful engineering assistant for a construction and EPC project.
Use the following retrieved context from project documents to answer the user's question.
If the answer is not contained in the context, say so clearly.

Context:
{context_block}

Question: {message}"""

        response = client.chat.completions.create(
            model="google/gemini-3.5-flash", 
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content

    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        reply = f"I'm sorry, I encountered an error communicating with the AI service: {e}"

    # 3. Store messages in DB
    user_msg = {
        "_id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "user",
        "content": message,
        "citations": None,
        "created_at": datetime.utcnow()
    }
    
    ai_msg = {
        "_id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "ai",
        "content": reply,
        "citations": json.dumps(citations),
        "created_at": datetime.utcnow()
    }
    
    await db.chat_messages.insert_many([user_msg, ai_msg])

    return reply
