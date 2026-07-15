from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.base import get_db
from app.modules.rfi.models import Rfi, ChatSession, ChatMessage
from app.modules.rfi.schemas import ChatRequest, ChatResponse, RfiCreate, RfiResponse, RfiResolveRequest
from app.modules.rfi.service import process_chat_message
from app.modules.auth.dependencies import get_authorized_project_id, get_current_user
from app.modules.auth.models import User

router = APIRouter()


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_id: str = Depends(get_authorized_project_id),
):
    """Ask a question against the project document corpus with RAG retrieval."""
    reply = await process_chat_message(db, request.session_id, request.message, project_id, current_user.id)
    return ChatResponse(reply=reply)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_id: str = Depends(get_authorized_project_id),
):
    """Ask a project-scoped question and preserve the auditable chat session."""
    reply = await process_chat_message(db, request.session_id, request.message, project_id, current_user.id)
    return ChatResponse(reply=reply)


@router.post("", response_model=RfiResponse, status_code=201)
async def create_rfi(
    rfi_in: RfiCreate,
    project_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a formal RFI."""
    rfi = Rfi(
        project_id=project_id,
        created_by=current_user.id,
        subject=rfi_in.subject,
        question=rfi_in.question,
    )
    db.add(rfi)
    await db.commit()
    await db.refresh(rfi)
    return rfi


@router.get("", response_model=list[RfiResponse])
async def list_rfis(
    project_id: str = Depends(get_authorized_project_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all RFIs, optionally filtered by project."""
    query = select(Rfi).order_by(Rfi.created_at.desc())
    query = query.where(Rfi.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{rfi_id}/resolve", response_model=RfiResponse)
async def resolve_rfi(
    rfi_id: str,
    resolve_in: RfiResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark an RFI as resolved with an answer."""
    result = await db.execute(select(Rfi).where(Rfi.id == rfi_id))
    rfi = result.scalars().first()
    if not rfi:
        raise HTTPException(status_code=404, detail="RFI not found")
    rfi.status = "answered"
    await db.commit()
    await db.refresh(rfi)
    return rfi
