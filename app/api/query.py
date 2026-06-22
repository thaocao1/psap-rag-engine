from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)
    include_sources: bool = True


class Source(BaseModel):
    document: str
    section: str
    chunk_text: str
    relevance_score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    model: str
    latency_ms: float


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Query the RAG pipeline with a question about emergency communications policy."""
    # Placeholder -- will be replaced with actual RAG pipeline
    return QueryResponse(
        answer=f"[Placeholder] Searching for: {request.question}",
        sources=[],
        model="placeholder",
        latency_ms=0.0,
    )
