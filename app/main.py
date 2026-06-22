from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.query import router as query_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize DB pool, load models, etc.
    yield
    # Shutdown: close connections


app = FastAPI(
    title="PSAP-RAG Engine",
    description="RAG pipeline for emergency communications policy retrieval",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(query_router, prefix="/api/v1")
