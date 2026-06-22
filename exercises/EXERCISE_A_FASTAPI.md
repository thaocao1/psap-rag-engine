# Exercise A: FastAPI Async Fundamentals (Hours 3-8)

**Goal:** Write FastAPI + Pydantic + async + tests without looking anything up.

**Time budget:** 6 hours across ~3 sessions. Not a tutorial -- build things, break things, fix things.

**Prerequisite check:** Run `python -m pytest tests/ -v` from project root. If 8 tests pass, the scaffold is working.

---

## Session 1: Core Mechanics (2 hours)

### 1.1 Path Parameters and Query Parameters (30 min)

Add a document retrieval endpoint to `app/api/query.py`:

```python
# GET /api/v1/documents/{doc_id}
# - Returns document metadata by ID
# - Query param: include_chunks (bool, default False)
# - If doc_id doesn't exist, return 404 with detail message
```

**Practice targets:**
- Path params with type hints (`doc_id: int`)
- Query params with defaults
- `HTTPException(status_code=404, detail="...")`
- Write 3 tests: happy path, 404, with include_chunks=True

### 1.2 Pydantic v2 Models (30 min)

Create `app/models/evaluation.py`:

```python
# EvalQuestion: question (str), expected_answer (str), expected_sources (list[str])
# EvalResult: question (str), retrieved_sources (list[str]), answer (str),
#             recall_at_k (float, 0-1), faithfulness (float, 0-1), latency_ms (float)
# EvalSuite: name (str), questions (list[EvalQuestion]), created_at (datetime)
# EvalReport: suite_name (str), results (list[EvalResult]),
#             mean_recall (computed), mean_faithfulness (computed)
```

**Practice targets:**
- `Field(...)` with constraints (`ge=0, le=1`)
- `@computed_field` or `@property` for mean_recall
- `model_validate()` and `model_dump()`
- `ConfigDict(json_schema_extra={"examples": [...]})`

### 1.3 Dependency Injection (30 min)

Create `app/dependencies.py`:

```python
# get_db() -> yields an async database session (mock for now)
# get_cohere_client() -> returns Cohere client (mock for now)
# require_api_key() -> validates X-API-Key header, raises 401
```

Wire into the query endpoint:
```python
@router.post("/query")
async def query_rag(request: QueryRequest, db=Depends(get_db), client=Depends(get_cohere_client)):
```

**Practice targets:**
- `Depends()` with generator functions (`yield`)
- `Header()` for API key extraction
- Override dependencies in tests with `app.dependency_overrides`

### 1.4 Structured Error Handling (30 min)

Add custom exception handler to `app/main.py`:

```python
# Custom exception class: RAGError(detail, error_code, status_code)
# Exception handler that returns structured JSON:
#   {"error": {"code": "RETRIEVAL_FAILED", "detail": "...", "timestamp": "..."}}
# Test: trigger the error, assert JSON structure
```

---

## Session 2: Async Patterns (2 hours)

### 2.1 asyncio.gather for Parallel Retrieval (45 min)

Create `app/services/retrieval.py`:

```python
async def dense_search(query: str, top_k: int) -> list[dict]:
    """Simulate pgvector cosine similarity search."""
    await asyncio.sleep(0.1)  # simulate DB latency
    return [{"text": f"Dense result {i}", "score": 0.9 - i*0.1} for i in range(top_k)]

async def sparse_search(query: str, top_k: int) -> list[dict]:
    """Simulate PostgreSQL ts_vector BM25 search."""
    await asyncio.sleep(0.08)
    return [{"text": f"Sparse result {i}", "score": 0.85 - i*0.1} for i in range(top_k)]

async def hybrid_search(query: str, top_k: int) -> list[dict]:
    """Run dense and sparse in parallel, merge with RRF."""
    dense_results, sparse_results = await asyncio.gather(
        dense_search(query, top_k),
        sparse_search(query, top_k),
    )
    return reciprocal_rank_fusion(dense_results, sparse_results)
```

**Practice targets:**
- `asyncio.gather()` for parallel execution
- Measure wall clock: hybrid should take ~max(0.1, 0.08) not sum
- RRF (Reciprocal Rank Fusion) scoring: `1/(k + rank)`
- `pytest-asyncio` for async test functions

### 2.2 Streaming Responses (30 min)

Add a streaming endpoint to `app/api/query.py`:

```python
# POST /api/v1/query/stream
# Returns StreamingResponse with SSE (Server-Sent Events)
# Each chunk: data: {"token": "word", "done": false}\n\n
# Final: data: {"token": "", "done": true, "sources": [...]}\n\n
```

**Practice targets:**
- `StreamingResponse(generate(), media_type="text/event-stream")`
- `async def generate(): yield f"data: {json}\n\n"`
- Test with `client.post(..., stream=True)` -- verify SSE format

### 2.3 Background Tasks (20 min)

Add logging of queries for analytics:

```python
# After returning response, log query + latency to a file (simulated DB write)
# Use FastAPI BackgroundTasks
@router.post("/query")
async def query_rag(request: QueryRequest, background_tasks: BackgroundTasks):
    response = await process_query(request)
    background_tasks.add_task(log_query, request.question, response.latency_ms)
    return response
```

### 2.4 Retry with Tenacity (25 min)

Create `app/services/llm.py`:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
async def call_llm(prompt: str, context: list[str]) -> str:
    """Call Cohere Command R+ with retry logic."""
    pass  # implement with httpx or cohere SDK
```

**Practice targets:**
- `tenacity` decorators
- Simulating failures in tests (first 2 calls fail, 3rd succeeds)
- Logging retry attempts

---

## Session 3: Testing & Integration (2 hours)

### 3.1 Comprehensive Test Patterns (45 min)

Add to `tests/`:

```python
# test_retrieval.py
# - Test hybrid_search returns merged results
# - Test RRF scoring is correct
# - Test parallel execution is actually parallel (wall clock assertion)

# test_dependencies.py
# - Test require_api_key accepts valid key
# - Test require_api_key rejects missing/invalid key
# - Test dependency override works in tests

# test_models.py
# - Test EvalResult validation (reject recall > 1.0)
# - Test EvalReport computed fields
# - Test model serialization round-trip
```

### 3.2 Prometheus Metrics (30 min)

Create `app/metrics.py`:

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

QUERY_COUNT = Counter("psap_rag_queries_total", "Total queries", ["status"])
QUERY_LATENCY = Histogram("psap_rag_query_latency_seconds", "Query latency")
RETRIEVAL_LATENCY = Histogram("psap_rag_retrieval_latency_seconds", "Retrieval latency", ["method"])

# Add /metrics endpoint
# Instrument query endpoint with timing
```

### 3.3 Structured Logging (25 min)

Configure `structlog` in `app/logging.py`:

```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# Use: logger.info("query_received", question=request.question, top_k=request.top_k)
# Output: {"event": "query_received", "question": "...", "top_k": 3, "level": "info", "timestamp": "..."}
```

### 3.4 Final Integration Test (20 min)

Write one end-to-end test that:
1. Creates a TestClient
2. Checks health
3. Posts a query
4. Verifies response structure
5. Checks metrics endpoint has incremented counters

---

## Completion Criteria

You're done with Exercise A when you can answer YES to all:

- [ ] Can you write a FastAPI endpoint with path params, query params, and Pydantic body without docs?
- [ ] Can you write a Pydantic v2 model with Field constraints, computed fields, and validators?
- [ ] Can you use Depends() for DB sessions, API keys, and service injection?
- [ ] Can you run two async tasks in parallel with asyncio.gather()?
- [ ] Can you write a streaming SSE endpoint?
- [ ] Can you write pytest tests with TestClient, including dependency overrides?
- [ ] Can you add Prometheus metrics to an endpoint?
- [ ] Can you configure structlog for JSON logging?

If yes -> move to Exercise B (Cohere API Deep Dive).
