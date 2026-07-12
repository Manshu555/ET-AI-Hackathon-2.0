from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from app.modules.rfi.models import ChatSession, ChatMessage
from app.modules.documents.models import DocumentChunk
from app.shared.ai.embedding_client import get_embedding
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

async def process_chat_message(db: AsyncSession, session_id: str, user_message: str) -> str:
    context_str = ""
    citations = []
    
    # --- 1. Try RAG retrieval from the database ---
    try:
        # Generate embedding for query
        query_embedding = get_embedding(user_message)
        
        # Retrieve all chunks and compute distance in Python (Hackathon SQLite Fallback)
        import numpy as np
        from scipy.spatial.distance import cosine
        
        query_stmt = select(DocumentChunk)
        result = await db.execute(query_stmt)
        chunks = result.scalars().all()
        
        if chunks:
            chunk_distances = []
            for chunk in chunks:
                if chunk.embedding:
                    try:
                        emb = json.loads(chunk.embedding)
                        if len(emb) == len(query_embedding):
                            dist = cosine(emb, query_embedding)
                            chunk_distances.append((dist, chunk))
                    except:
                        pass
            
            # Sort by distance (lower is better) and take top 5
            chunk_distances.sort(key=lambda x: x[0])
            top_chunks = [c[1] for c in chunk_distances[:5]]
            
            context_texts = []
            for chunk in top_chunks:
                context_texts.append(f"Source ID [{chunk.id}]: {chunk.chunk_text}")
                citations.append(chunk.id)
                
            context_str = "\n\n".join(context_texts)
    except Exception as e:
        logger.warning(f"Database/RAG error (running in fallback mode): {e}")
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
Use the following context from project documents to answer the question. Cite your sources using the Source IDs provided.

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
    
    # --- 3. Try to persist messages to DB (non-fatal if DB is offline) ---
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
