import time
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.retrieval_service import retrieve, RetrievedResult
from app.services.llm_service import generate_answer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User's natural language question")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to retrieve")


class RetrievedSource(BaseModel):
    song_id: int
    title: str
    movie: str | None = None
    matched_text: str | None = None
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[RetrievedSource] = []
    retrieval_type: str = "none"
    latency_ms: float = 0.0


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """RAG-powered chat endpoint for answering questions about Tamil songs."""
    start_time = time.perf_counter()

    question_clean = request.question.strip()
    if not question_clean:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # 1. Retrieve relevant sources (multi-stage routing: Title -> SQL -> Semantic)
        results, retrieval_type = retrieve(question_clean, db, top_k=request.top_k)

        # 2. Build context string for the LLM
        if results:
            context_blocks = [
                f"Song: {r.title} (Movie: {r.movie or 'N/A'})\nText: {r.chunk_text}"
                for r in results
            ]
            context = "\n---\n".join(context_blocks)
        else:
            context = ""

        # 3. Generate grounded answer using Gemini LLM service
        answer = generate_answer(question_clean, context)

        # 4. Map results to response schema
        sources = [
            RetrievedSource(
                song_id=r.song_id,
                title=r.title,
                movie=r.movie,
                matched_text=r.chunk_text,
                score=r.score,
            )
            for r in results
        ]

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return ChatResponse(
            answer=answer,
            sources=sources,
            retrieval_type=retrieval_type,
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.error(f"Error in RAG chat endpoint: {e}", exc_info=True)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        # Graceful fallback: never crash with unhandled 500 if possible
        return ChatResponse(
            answer="I encountered an unexpected error processing your request. Please try again.",
            sources=[],
            retrieval_type="error",
            latency_ms=latency_ms,
        )
