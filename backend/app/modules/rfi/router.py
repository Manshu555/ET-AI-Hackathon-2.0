from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.modules.rfi.schemas import ChatRequest, ChatResponse
from app.modules.rfi.service import process_chat_message

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    reply = await process_chat_message(db, request.session_id, request.message)
    return ChatResponse(reply=reply)
