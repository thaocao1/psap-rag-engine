# PSAP-RAG Engine

Production RAG pipeline for emergency communications policy retrieval, built for the domain where "hallucination" isn't an academic problem -- it's a liability.

## What This Does

Answers questions like *"What is the correct MSAG validation procedure when a call presents with a mismatched ESN?"* by retrieving and synthesizing information from NENA standards, FCC E911 orders, and operational runbooks.

## Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              PSAP-RAG Engine                │
                    │                                             │
   Query ──────►   │  FastAPI Gateway (rate limit, auth, DLP)    │
                    │         │                                   │
                    │         ▼                                   │
                    │  Embedding (Cohere Embed v3)               │
                    │         │                                   │
                    │         ▼                                   │
                    │  Hybrid Search                              │
                    │  ├── Dense: pgvector (cosine, HNSW)        │
                    │  └── Sparse: PostgreSQL ts_vector (BM25)   │
                    │         │                                   │
                    │         ▼                                   │
                    │  Reranking (Cohere Rerank 3)               │
                    │         │                                   │
                    │         ▼                                   │
                    │  Generation (Cohere Command R+)            │
                    │  └── Grounded with citations               │
                    │         │                                   │
                    │         ▼                                   │
                    │  Guardrails                                 │
                    │  └── Out-of-scope classifier               │
                    │                                             │
                    └─────────────────────────────────────────────┘

   Observability: Langfuse traces per stage
   Evaluation: RAGAS framework (recall@k, faithfulness, relevance)
   Deployment: Helm chart for OpenShift / any K8s
```

## Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API | FastAPI (async) | Production async, Pydantic validation, OpenAPI docs |
| Embeddings | Cohere Embed v3 | `input_type` parameter, multilingual, 1024-dim |
| Vector Store | PostgreSQL + pgvector | Operational simplicity over managed vector DBs at this corpus size |
| Sparse Search | PostgreSQL ts_vector | Native, no additional infra |
| Reranker | Cohere Rerank 3 | Cross-encoder precision that bi-encoders cannot match |
| Generation | Cohere Command R+ | Native grounding with `documents=`, built-in citation |
| Cache | Redis | Embedding cache, frequent query cache |
| Observability | Langfuse + Prometheus/Grafana | LLM-specific traces + infrastructure metrics |
| Deployment | Helm + Docker Compose | OpenShift-ready, also runs locally |

## Evaluation

Custom evaluation harness with 50 golden Q&A pairs from NENA/FCC domain:

| Metric | Target | Description |
|--------|--------|-------------|
| Context Recall@3 | > 0.85 | Relevant chunks in top-3 results |
| Context Precision | > 0.80 | Proportion of retrieved chunks that are relevant |
| Answer Faithfulness | > 0.90 | Answer grounded in retrieved context |
| Answer Relevance | > 0.85 | Answer addresses the question asked |
| Latency (P99) | < 2s | End-to-end at 50 concurrent queries |

## Key Design Decisions (ADRs)

- **ADR-001: pgvector over Pinecone** -- Operational simplicity matters more than benchmark performance at corpus sizes under 100K documents. One fewer managed service, same PostgreSQL backup/restore procedures the team already knows.
- **ADR-002: Semantic chunking over fixed-size** -- NENA standards have section numbering, cross-references, and hierarchical structure. `RecursiveCharacterTextSplitter(chunk_size=512)` produces garbage on structured regulatory documents.
- **ADR-003: Hybrid search (dense + sparse) with RRF** -- Regulatory queries mix exact terminology ("MSAG", "ESN", "PSAP") with semantic intent. Dense-only misses exact acronym matches; sparse-only misses paraphrased questions.

## Running Locally

```bash
# Prerequisites: Docker, Python 3.11+
docker compose up -d  # PostgreSQL + pgvector, Redis, Langfuse

pip install -r requirements.txt
python -m app.ingest --source data/nena_standards/
python -m app.eval --suite golden_qa.json

uvicorn app.main:app --reload
```

## Running on OpenShift

```bash
helm install psap-rag ./helm/psap-rag \
  --set cohere.apiKey=$COHERE_API_KEY \
  --set postgresql.persistence.size=10Gi \
  --namespace psap-rag --create-namespace
```

## Project Status

| Phase | Status |
|-------|--------|
| Data pipeline (ingest, chunk, embed) | In Progress |
| Hybrid search + reranking | Planned |
| Evaluation harness | Planned |
| Guardrails | Planned |
| Helm chart | Planned |
| Load testing | Planned |

## Why This Project

I've operated 911/PSAP infrastructure for 15 years. This RAG pipeline answers the same questions dispatchers and supervisors ask during incidents -- but retrieves from authoritative sources instead of memory. The domain expertise isn't simulated; it's the reason the chunking strategy, evaluation questions, and guardrails are realistic.

---

*Part of the [public-sector-ai-reference-arch](../public-sector-ai-reference-arch) portfolio. See also: [incident-response-agent](../incident-response-agent), [airgap-llm-framework](../airgap-llm-framework)*
