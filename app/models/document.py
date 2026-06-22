from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    id: str
    document_name: str
    section_title: str
    chunk_index: int
    text: str
    token_count: int
    embedding: list[float] | None = None
    metadata: dict = Field(default_factory=dict)


class IngestResult(BaseModel):
    document_name: str
    chunks_created: int
    total_tokens: int
    embedding_model: str
