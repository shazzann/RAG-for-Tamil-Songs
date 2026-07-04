from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """RAG-powered chat endpoint for answering questions about Tamil songs."""
    # TODO: implement RAG pipeline
    return ChatResponse(
        answer="RAG pipeline not yet implemented.",
        sources=[],
    )
