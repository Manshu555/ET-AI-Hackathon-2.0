from fastapi import APIRouter, Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.base import get_db
from app.modules.rfi.schemas import ChatRequest, ChatResponse, RfiCreate, RfiResponse, RfiResolveRequest
from app.modules.rfi.service import process_chat_message
from app.modules.auth.dependencies import get_current_user
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Ask a question against the project document corpus with RAG retrieval."""
    reply = await process_chat_message(db, request.session_id, request.message)
    return ChatResponse(reply=reply)

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Legacy chat endpoint (no auth required for demo)."""
    # Auto-create dummy session if it doesn't exist
    session = await db.chat_sessions.find_one({"_id": request.session_id})
    if not session:
        await db.chat_sessions.insert_one({
            "_id": request.session_id,
            "project_id": None,
            "user_id": "demo",
            "created_at": datetime.utcnow()
        })
        
    reply = await process_chat_message(db, request.session_id, request.message)
    return ChatResponse(reply=reply)

@router.post("", response_model=RfiResponse, status_code=201)
async def create_rfi(
    rfi_in: RfiCreate,
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a formal RFI."""
    rfi = {
        "_id": str(uuid.uuid4()),
        "project_id": project_id,
        "created_by": current_user["_id"],
        "subject": rfi_in.subject,
        "question": rfi_in.question,
        "status": "open",
        "created_at": datetime.utcnow()
    }
    await db.rfis.insert_one(rfi)
    rfi["id"] = rfi.pop("_id")
    return rfi

@router.get("", response_model=list[RfiResponse])
async def list_rfis(
    project_id: str = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List all RFIs, optionally filtered by project."""
    query = {}
    if project_id:
        query["project_id"] = project_id
        
    rfis = []
    async for rfi in db.rfis.find(query).sort("created_at", -1):
        rfi["id"] = rfi.pop("_id")
        rfis.append(rfi)
    return rfis

@router.patch("/{rfi_id}/resolve", response_model=RfiResponse)
async def resolve_rfi(
    rfi_id: str,
    resolve_in: RfiResolveRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Mark an RFI as resolved with an answer."""
    rfi = await db.rfis.find_one({"_id": rfi_id})
    if not rfi:
        raise HTTPException(status_code=404, detail="RFI not found")
        
    await db.rfis.update_one({"_id": rfi_id}, {"$set": {"status": "answered"}})
    
    rfi = await db.rfis.find_one({"_id": rfi_id})
    rfi["id"] = rfi.pop("_id")
    return rfi
