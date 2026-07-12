> **Scope note.** This document is the **target production architecture** for EPC-Intel — the system the 48-hour hackathon MVP is a deliberate, descoped first slice of. It is **not** a build plan for the hackathon itself. Where this document specifies Kubernetes, Celery/Redis, multi-service decomposition, or a four-week roadmap, that is intentional: those are the right choices at production scale (thousands of RFIs, 15,000–40,000 line items, multi-tenant regulated data) and the wrong choices for a 48-hour, four-developer build, which is why the hackathon guide strips them out. Use this document to answer due-diligence questions about where the platform goes after the demo, not as hackathon instructions.

---

# EPC-Intel: Production Implementation Guide
### AI-Powered EPC Project Intelligence Platform for Data Centre Construction
**Document class:** Engineering implementation blueprint · **Audience:** Engineering team building the post-hackathon production system · **Status:** v1.0

---

## Table of Contents

1. Executive Summary
2. System Overview
3. Technology Stack
4. Complete Architecture
5. Detailed Module Design
6. AI Architecture
7. RAG Pipeline
8. Database Design
9. API Design
10. Background Jobs
11. Deployment Architecture
12. Security
13. Performance Optimization
14. Failure Recovery
15. Development Roadmap
16. Testing Strategy
17. Cost Estimation
18. Future Enhancements
19. Appendix

---

## 1. Executive Summary

### 1.1 Problem Statement

A hyperscale data-centre EPC project generates 15,000–40,000 equipment line items, involves up to 200 concurrent trade contractors, and runs commissioning sequences spanning thousands of individual test procedures — with zero tolerance for the kind of error that compromises a future uptime SLA. A 2024 Turner & Townsend survey found 67% of Asia-Pacific data-centre EPC projects overran schedule by more than 10%, with procurement misalignment and commissioning failures as the leading causes. The root cause is not a shortage of data; it is fragmentation: specifications, submittals, test records, RFI logs, and change orders live in disconnected systems, and no system connects them fast enough to change a decision before it becomes a schedule slip.

### 1.2 Business Motivation

India's data-centre capacity is projected to grow from ~900 MW (2024) to 2,700+ MW by 2027, representing $15B+ of capital deployment. Existing construction-management incumbents (Procore, Autodesk Construction Cloud, Oracle Aconex) have generalized AI layers — contextual chat, checklist scanning, correspondence categorization — but none ship a deterministic, safety-critical numeric-compliance layer purpose-built for data-centre tolerances (clearances, voltages, redundancy ratings). That is the wedge this platform is built around.

### 1.3 Current Industry Limitations

| Limitation | Consequence |
|---|---|
| Specs, submittals, schedules, and test logs in separate systems | Manual cross-referencing; deviations caught late or not at all |
| Generalized LLM chat layers with no deterministic backstop | Hallucinated numeric tolerances on safety-critical clauses |
| Reactive schedule tracking | Risks surface after they are already schedule-critical, not weeks ahead |
| Paper-based or siloed commissioning records | No queryable as-built quality record for Tier III/IV certification |

### 1.4 Objectives

- Unify documents, schedules, procurement, and quality records into one queryable intelligence layer.
- Catch specification deviations before they reach site, with a false-negative rate low enough to be trusted on safety-critical clauses.
- Predict schedule risk 2–4 weeks ahead of a critical-path slip, with a heuristic and later an ML model that beats a naive baseline.
- Provide an auditable, tenant-isolated system of record suitable for regulated, multi-client deployment.

### 1.5 Expected Benefits

- Reduction in manual cross-referencing hours per submittal review (target: hours, not percentages — see hackathon guide §9.1 for how this is measured empirically rather than projected).
- Earlier detection of schedule risk, reducing rework and expediting costs.
- A defensible, auditable compliance trail suitable for Tier III/IV commissioning sign-off.

---

## 2. System Overview

### 2.1 Architecture Principles

1. **Deterministic where possible, probabilistic only where necessary.** Every AI component must be justified against a deterministic alternative; numeric/quantitative checks are never LLM-only.
2. **Multi-tenant isolation enforced at the database layer**, not the application layer — a single missing `WHERE` clause must never be able to leak data between tenants.
3. **Each service independently scalable and independently failable.** No single service's outage should take down ingestion, retrieval, and compliance simultaneously.
4. **Every AI output is citeable.** No answer is presented to a user without a traceable source document and page.
5. **Cost is a first-class design constraint**, not an afterthought — token budgets and caching are designed in from day one.

### 2.2 Major Components

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        WEB[Next.js Web App]
        MOB[Mobile / Field App]
    end

    subgraph Edge["Edge"]
        CDN[CDN / Static Assets]
        GW[API Gateway]
    end

    subgraph App["Application Layer"]
        AUTH[Auth Service]
        DOC[Document Service]
        COMP[Compliance Service]
        RFI[Knowledge / RFI Service]
        SCHED[Schedule Risk Service]
        PROC[Procurement Service]
        COMM[Commissioning Service]
        NOTIF[Notification Service]
        DASH[Dashboard / Aggregation Service]
    end

    subgraph AI["AI / ML Layer"]
        EMB[Embedding Service]
        CV[Computer Vision Service]
        RULE[Deterministic Rule Engine]
        LLM[LLM Gateway]
        MLRISK[Schedule Risk Model]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL + pgvector)]
        REDIS[(Redis Cache / Broker)]
        S3[(Object Storage)]
    end

    subgraph Async["Background Processing"]
        CELERY[Celery Workers]
        DLQ[Dead Letter Queue]
    end

    subgraph Obs["Observability"]
        LOG[Structured Logging]
        MET[Metrics / Prometheus]
        TRACE[Tracing]
        ALERT[Alerting]
    end

    WEB --> CDN --> GW
    MOB --> GW
    GW --> AUTH
    GW --> DOC
    GW --> COMP
    GW --> RFI
    GW --> SCHED
    GW --> PROC
    GW --> COMM
    GW --> DASH

    DOC --> S3
    DOC --> CELERY
    CELERY --> EMB
    CELERY --> CV
    EMB --> PG
    CV --> PG

    COMP --> RULE
    COMP --> LLM
    COMP --> PG
    RFI --> LLM
    RFI --> PG
    SCHED --> MLRISK
    MLRISK --> PG

    CELERY --> REDIS
    CELERY --> DLQ
    NOTIF --> REDIS

    App --> Obs
    AI --> Obs
    Async --> Obs
```

### 2.3 High-Level Workflow

1. A Project Manager provisions a project and uploads governing documents (specs, standards, schedule export, submittals, drawings).
2. The Document Service stores originals in object storage and enqueues an ingestion job.
3. Celery workers run OCR/parsing, chunking, and embedding generation asynchronously; the Computer Vision service processes drawings in parallel.
4. As submittals arrive, the Compliance Service runs the dual-layer (LLM + deterministic) check and writes findings to `deviations`.
5. The Schedule Risk Service recomputes per-task risk scores on a scheduled cadence and on schedule-data updates.
6. The Notification Service pushes alerts (Slack/email/in-app) on high-severity deviations or risk-threshold breaches.
7. The Dashboard Service aggregates cross-module KPIs for PM and executive views.

---

## 3. Technology Stack

| Layer | Technology | Why chosen | Primary alternative considered | Why not chosen |
|---|---|---|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui | Server components reduce client bundle for document-heavy views; strong ecosystem for citation-linked chat UIs | Remix | Smaller ecosystem for this team's component needs; no material advantage at this scale |
| Backend | FastAPI (Python 3.12) | Native async, Pydantic validation matches the JSON-heavy AI payload shapes, first-class OpenAPI generation for the API contracts in §9 | Django REST Framework | Heavier ORM/ceremony for a service that is mostly async I/O and AI orchestration, not CRUD-heavy admin |
| Primary database | PostgreSQL 16 | ACID system of record; `pgvector` extension collapses relational and vector storage into one operationally simple system; Row-Level Security gives database-enforced multi-tenancy | Separate relational DB + dedicated vector DB (Qdrant/Weaviate) | Two systems to keep in sync and secure; pgvector's HNSW index closes most of the recall gap at this corpus scale (see hackathon guide §3.1 for the explicit trade-off analysis) |
| Object storage | S3-compatible (AWS S3 / MinIO for on-prem) | Standard, cheap, versioned storage for source PDFs/drawings | Filesystem storage | Does not scale across multiple app instances; no built-in versioning |
| Vector index | pgvector (HNSW) | Avoids a second data store; HNSW does not require periodic reindexing as data grows, unlike IVFFLAT | Pinecone / Qdrant managed | Justified only past a corpus size where pgvector's single-node limits are actually hit — see §13.4 scaling trigger |
| Authentication | JWT (short-lived access token) + httpOnly refresh cookie + CSRF token | Stateless access tokens scale horizontally; httpOnly cookie mitigates XSS; explicit CSRF token closes the remaining CSRF gap | Session-based auth | Requires sticky sessions or a shared session store, adding an operational dependency for no security benefit here |
| Message queue / broker | Redis (Celery broker) | Simple operationally, sufficient throughput for document-ingestion-scale job volumes | RabbitMQ / Kafka | Kafka's ordering/replay guarantees are not needed at this job volume; adds operational overhead |
| Caching | Redis | Response caching for near-duplicate RFI queries (embedding-similarity keyed); session and rate-limit counters | Application-level in-memory cache | Does not survive process restarts or scale across instances |
| AI frameworks | Native LLM provider SDKs (Anthropic/OpenAI) with a hand-rolled tool-calling loop; Ultralytics YOLO11 for CV | Full control over the ReAct loop's retry/self-correction logic without framework boilerplate; YOLO11 is a mature, well-documented detector | LangGraph | Graph-based orchestration is valuable for multi-agent, human-in-the-loop production workflows — reconsider once the agent surface grows past a single-agent loop (see §18.3) |
| Background jobs | Celery + Redis, with a Dead Letter Queue | Mature retry/backoff semantics; DLQ isolates poison-pill ingestion jobs from blocking the queue | AWS SQS + Lambda | Team already standardized on Celery for local-dev parity; revisit if moving fully serverless |
| Deployment | Docker Compose (staging) → Kubernetes (production) | Compose is sufficient until multi-region/auto-scaling requirements appear; Kubernetes gives horizontal pod autoscaling and rolling deploys when they do | Serverless (Cloud Run / Lambda) | Long-running ingestion and CV inference jobs exceed typical serverless execution-time limits without added complexity |
| Monitoring | Prometheus + Grafana, structured JSON logs, OpenTelemetry tracing | Standard, self-hostable, avoids vendor lock-in | Datadog | Cost scales unfavorably at this log/metric volume for an early-stage product |

---

## 4. Complete Architecture

### 4.1 Request-Level Sequence: Compliance Check

```mermaid
sequenceDiagram
    participant U as User (PM)
    participant FE as Next.js Frontend
    participant GW as API Gateway
    participant CS as Compliance Service
    participant RULE as Rule Engine
    participant LLM as LLM Gateway
    participant PG as PostgreSQL

    U->>FE: Upload submittal
    FE->>GW: POST /submittals
    GW->>CS: Create submittal record
    CS->>PG: INSERT submittals
    CS-->>FE: 202 Accepted (job queued)
    Note over CS: Async: retrieve matching spec clauses
    CS->>PG: Hybrid search (BM25 + pgvector + RRF)
    PG-->>CS: Top-k spec clauses
    par Parallel dual-layer check
        CS->>LLM: Semantic compliance read
        LLM-->>CS: Compliance verdict + rationale
    and
        CS->>RULE: Structured numeric cross-check
        RULE-->>CS: Pass/fail + extracted constraint
    end
    CS->>CS: Reconcile (rule engine wins on numeric disagreement)
    CS->>PG: INSERT deviations (detected_by tag)
    CS-->>FE: Webhook / poll: findings ready
    FE-->>U: Render findings with citations
```

### 4.2 Deployment Topology

```mermaid
flowchart LR
    subgraph Internet
        USER[Users]
    end
    subgraph CDN_Layer["CDN"]
        CDN[CloudFront / Vercel Edge]
    end
    subgraph K8S["Kubernetes Cluster"]
        subgraph Ingress
            ING[Ingress Controller]
        end
        subgraph Services
            SVC1[FastAPI Pods x N]
            SVC2[Celery Worker Pods x N]
            SVC3[CV Inference Pods - GPU node pool]
        end
        HPA[Horizontal Pod Autoscaler]
    end
    subgraph Managed["Managed Data Services"]
        RDS[(PostgreSQL - Managed, pgvector enabled)]
        REDISM[(Redis - Managed)]
        S3M[(Object Storage)]
    end
    subgraph ObsStack["Observability"]
        PROM[Prometheus]
        GRAF[Grafana]
    end

    USER --> CDN --> ING
    ING --> SVC1
    SVC1 --> RDS
    SVC1 --> REDISM
    SVC1 --> S3M
    SVC1 --> SVC2
    SVC2 --> RDS
    SVC2 --> S3M
    SVC3 --> S3M
    SVC3 --> RDS
    HPA -.-> SVC1
    HPA -.-> SVC2
    Services --> PROM --> GRAF
```

---

## 5. Detailed Module Design

Each module below follows the same template: purpose, responsibilities, I/O, API, schema, data flow, error handling, caching, security, and scaling notes. Modules with substantially similar shapes are grouped to avoid repetition.

### 5.1 Authentication Module

**Purpose:** Issue and validate identity, enforce tenant context on every request.

**Responsibilities:** Login/refresh/logout, JWT issuance, RBAC role assignment, tenant-context injection for RLS.

**Input:** Credentials (email/password or SSO assertion). **Output:** Access token (15 min TTL), refresh cookie (7 day TTL, httpOnly, `SameSite=Strict`).

**REST API:**

| Method | Endpoint | Auth | Notes |
|---|---|---|---|
| POST | `/auth/login` | None | Rate-limited 5/min/IP |
| POST | `/auth/refresh` | Refresh cookie + CSRF header | Rotates refresh token |
| POST | `/auth/logout` | Access token | Revokes refresh token server-side |

**Database tables:** `users(id, email, password_hash, role, project_ids[])`, `refresh_tokens(id, user_id, token_hash, expires_at, revoked_at)`.

**Error handling:** Invalid credentials → 401 with generic message (no user-enumeration leak). Expired refresh token → 401, force re-login. Missing CSRF header on refresh → 403.

**Caching:** None for auth decisions (correctness-critical); revocation list cached in Redis with a short TTL to avoid a DB round-trip on every request.

**Security:** Passwords hashed with Argon2id. Refresh tokens stored hashed, never in plaintext. Failed-login counter triggers exponential backoff per account.

**Scaling:** Stateless access-token validation scales horizontally with no shared state; only refresh/revocation requires a DB or Redis round-trip.

### 5.2 Document Upload Module

**Purpose:** Accept and durably store source documents; kick off the ingestion pipeline.

**API:** `POST /projects/{id}/documents` (multipart upload, max 200MB/file) → `202 { document_id, status: "queued" }`.

**Database:** `documents(id, project_id, filename, s3_key, version, is_active, uploaded_by, uploaded_at, page_count, ingestion_status)`.

**Data flow:** Client → API Gateway → Document Service → S3 (original) → enqueue `ingest_document` Celery task → status polled via `GET /documents/{id}`.

**Error handling:** Virus scan failure → reject with `422`. Unsupported MIME type → `415`. S3 upload failure → retry 3x with exponential backoff, then `503` to client with a re-upload prompt.

**Retry mechanism:** Ingestion task retries transient failures (network, rate limit) up to 5 times with jittered exponential backoff; permanent failures (corrupt PDF) route to the Dead Letter Queue (§10.3) for manual review.

**Security:** Signed, time-limited S3 URLs for retrieval; virus scanning (ClamAV) before persisting; per-tenant S3 prefix isolation as defense-in-depth alongside RLS.

### 5.3 OCR Pipeline Module

**Purpose:** Extract text from scanned, low-DPI, or handwritten-annotation pages that standard text extraction cannot handle.

**Flow:** PyMuPDF attempts native text extraction first (fast, free). If extracted text has a garbled-character ratio above threshold (e.g., >15% non-dictionary tokens), the page image is routed to a vision-language model for direct text extraction. Both paths converge on a common `PageText` object consumed by the Chunking module.

**Failure modes:** VLM extraction low-confidence → page flagged `needs_review` in the UI rather than silently accepted. OCR queue backlog → surfaced as a Prometheus gauge (`ocr_queue_depth`) with alerting past a threshold.

### 5.4 Document Parser & Chunking Module

**Purpose:** Convert raw page text into layout-aware, retrieval-ready chunks.

**Responsibilities:** Detect headers/section hierarchy, keep tables intact (never split a table row across chunks), attach `page_number` and `section_path` metadata.

**Output schema:** `document_chunks(id, document_id, chunk_text, section_path, page_number, embedding vector(1024), is_active, superseded_by, created_at)`, HNSW-indexed on `embedding`.

**Versioning:** On re-ingestion of a newer document version, chunks from the prior version are marked `is_active = false` and `superseded_by` set to the new chunk IDs, so retrieval never surfaces a stale, superseded clause alongside a current one.

### 5.5 Embedding Generation Module

**Purpose:** Generate dense vector representations for each chunk.

**Model:** `bge-large-en-v1.5` (open-weight, self-hostable) as primary; hosted API embedding model as an automatic fallback if the self-hosted inference endpoint is unhealthy.

**Batching:** Embeddings generated in batches of 64 chunks per call to amortize inference overhead; batch failures retry at the individual-chunk level, not the whole batch, to avoid re-computing successful embeddings.

### 5.6 Vector Search Module

**Purpose:** Hybrid lexical + dense retrieval, fused via Reciprocal Rank Fusion (RRF). See §7 for the full RAG pipeline treatment.

### 5.7 Compliance Engine Module

**Purpose:** The platform's core differentiator — dual-layer LLM + deterministic numeric compliance checking. Full design in the hackathon guide §6; production hardening adds:

- A **confidence-scored review queue**: findings below a configurable confidence threshold route to a human reviewer instead of auto-publishing, with the review decision fed back as a labeled training example for periodic prompt/rule tuning.
- **Versioned rule definitions**: the structured-constraint extraction rules are themselves versioned (`rule_version` column on `deviations`) so a rule change can be audited against historical findings.

**Sequence diagram:** see §4.1.

### 5.8 Knowledge Assistant (RFI) Module

**Purpose:** Conversational, citation-grounded Q&A over the full project document corpus, plus RFI de-duplication (semantic search against previously-answered RFIs before creating a new one).

**API:** `POST /projects/{id}/rfi/query { question }` → `{ answer, citations: [{document_id, page_number, excerpt}], similar_rfis: [...] }`.

**Caching:** Query embeddings compared against a cache of prior query embeddings; a cosine-similarity hit above 0.85 returns the cached answer with zero LLM cost (see §13.1 and hackathon guide §10).

### 5.9 Schedule Intelligence Module

**Purpose:** Predict per-task delay risk from procurement status, lead times, workforce availability, and weather.

**Model progression:** naive baseline (all tasks on-time) → logistic regression → LightGBM, each required to beat the previous on a strictly time-based holdout split (AUC for classification, MAE for delay-day regression). SHAP values expose the top contributing factors per prediction. Full justification in hackathon guide §8.

### 5.10 Procurement Intelligence Module

**Purpose:** Geospatial tracking of critical equipment shipments (UPS, generators, chillers, switchgear) with at-risk-delivery alerting.

**Data sources:** Manual status entry (v1), carrier tracking API integration (v2), AIS/logistics feeds for ocean freight (v3 — see §18).

**Database:** `shipments(id, project_id, equipment_tag, carrier, current_location geography, eta, status, risk_score)`.

### 5.11 Commissioning Intelligence Module

**Purpose:** Guided TIA-942/BICSI/Uptime-Tier test sequences with auto-generated test records and non-conformance flagging.

**Design note:** Standards content (TIA-942, BICSI) is proprietary; production deployment requires a licensing agreement before seeding templates — track this as a legal dependency, not an engineering one.

### 5.12 Notification Engine

**Purpose:** Route high-severity findings and risk-threshold breaches to the right person through the right channel.

**Design:** Rule-based routing table (`severity × role × channel`) rather than an AI-driven routing decision — this is a case where a deterministic lookup table outperforms and is more auditable than an ML classifier, consistent with the "deterministic where possible" principle in §2.1.

### 5.13 Executive Dashboard Module

**Purpose:** Cross-module KPI aggregation (open deviations by severity, schedule risk trend, procurement at-risk count, commissioning progress).

**Design:** Pre-aggregated materialized views refreshed on a schedule (not computed live per request) to keep dashboard load times independent of underlying data volume.

### 5.14 Audit Log Module

**Purpose:** Immutable, queryable record of every override, dismissal, and manual edit — required for regulated construction compliance, modeled on Oracle Aconex's unalterable audit trail.

**Database:** `audit_logs(id, user_id, action, entity_type, entity_id, metadata jsonb, created_at)` — insert-only, no `UPDATE`/`DELETE` grants at the database role level, enforced independently of application logic.

---

## 6. AI Architecture

Every AI component below is included because a deterministic alternative was evaluated and found insufficient; where a deterministic approach *is* sufficient (Notification routing, RLS enforcement, numeric clause parsing), it is used instead and is *not* listed here.

### 6.1 Compliance Semantic Reader (LLM)

- **Purpose:** Read a spec clause and a submittal excerpt and produce a natural-language compliance judgment plus rationale, for clauses that are not purely numeric (e.g., "shall be installed in accordance with manufacturer's recommendations").
- **Input:** Clause text, submittal excerpt, prior similar-clause judgments (few-shot context).
- **Output:** `{ verdict: compliant | deviation | needs_review, rationale, confidence }`.
- **Prompt engineering:** System prompt fixes the output schema; the model is explicitly instructed that numeric clauses are handled by a separate deterministic engine and it should defer, not compute, on those.
- **Evaluation:** Precision/recall against the 100-item labeled evaluation set (hackathon guide §9.1), re-run on every prompt change as a regression gate.
- **Failure modes:** Ambiguous clause language → low confidence, routed to human review rather than auto-published. Context-window truncation on very long clauses → chunking ensures no single clause exceeds a safe token budget.
- **Latency:** 2–6s typical; not on the critical path of ingestion, only of the async compliance-check job.
- **Cost:** Capped by hybrid-search top-k retrieval (§7) limiting context size; cached for identical clause/submittal pairs.
- **Fallback:** Self-hosted open-weight model (Llama 3 70B class) behind the same interface if the primary hosted model is unavailable or a data-residency constraint applies.

### 6.2 Deterministic Numeric Rule Engine

Not an ML model — included here because it is the direct counterpart to 6.1 and the reconciliation logic between the two is central to the platform. See hackathon guide §6 for the structured-constraint extraction design.

### 6.3 Computer Vision — Drawing Review (YOLO11 + Eigen-CAM)

- **Purpose:** Detect engineering symbols and dimension annotations on P&IDs/electrical drawings; flag clearance violations; explain detections visually.
- **Training data:** Fine-tuned on a labeled corpus of data-centre P&ID symbols (valves, CRAC units, panels); cold-start with a pretrained COCO/industrial-symbol checkpoint and active-learning-label the highest-uncertainty detections first.
- **Evaluation:** mAP@0.5 against a held-out labeled drawing set; clearance-violation precision/recall tracked separately from raw detection accuracy, since the business-critical metric is "did we flag the right violations," not "did we draw a box around every symbol."
- **Latency:** CV inference isolated to a GPU-backed node pool so a burst of drawing uploads cannot starve the CPU-bound API pods.
- **Fallback:** If GPU inference capacity is saturated, jobs queue rather than fall back to a degraded CPU path with materially worse latency — an explicit queue-depth alert is preferred over a silent quality regression.

### 6.4 Schedule Risk Model

Covered in §5.9; production adds continuous retraining on a monthly cadence with drift monitoring (population stability index on the input feature distributions) to catch when the model's operating conditions have shifted enough to warrant retraining.

### 6.5 Embedding Model

Covered in §5.5.

### 6.6 Cross-Cutting: Prompt Injection & Hallucination Controls

- Documents ingested from third parties (vendor submittals) are never given tool-calling privileges — only read access to their own extracted text, never the ability to trigger actions.
- Every LLM-generated compliance verdict is cross-checked against the deterministic engine on numeric clauses (§6.2) as the primary hallucination defense.
- Citation generation (§7) means every RFI-chat answer is checkable against its source; answers without a retrievable citation are suppressed rather than shown unsourced.

---

## 7. RAG Pipeline

### 7.1 Chunking

Layout-aware splitting that respects header hierarchy and table boundaries (§5.4) — never a fixed token-count splitter, which risks bisecting a table row and destroying the row's semantic integrity.

### 7.2 Embedding

`bge-large-en-v1.5`, 1024-dimensional, batched (§5.5).

### 7.3 Vector Database

PostgreSQL + pgvector, HNSW index (`vector_cosine_ops`). HNSW chosen over IVFFLAT specifically because it does not require periodic reindexing as the corpus grows — critical given a single hyperscale project can generate hundreds of thousands of chunks over its lifecycle.

### 7.4 Hybrid Search

```sql
-- Lexical component (PostgreSQL full-text search)
SELECT id, ts_rank(text_search_vector, query) AS lexical_score
FROM document_chunks, plainto_tsquery('english', :query) query
WHERE text_search_vector @@ query AND is_active = true AND project_id = :project_id
ORDER BY lexical_score DESC LIMIT 50;

-- Dense component (pgvector cosine similarity)
SELECT id, 1 - (embedding <=> :query_embedding) AS dense_score
FROM document_chunks
WHERE is_active = true AND project_id = :project_id
ORDER BY embedding <=> :query_embedding LIMIT 50;
```

Both result sets are fused with Reciprocal Rank Fusion (`score = Σ 1 / (k + rank_i)`, `k = 60` typical) so a chunk ranking well on both lexical and semantic relevance surfaces at the top, while a chunk that only one method would have found still gets a fair chance to be retrieved.

### 7.5 Reranking

For the top ~50 RRF-fused candidates, an optional cross-encoder reranking pass (e.g., a `bge-reranker` model) re-scores the candidate set before the final top-k is selected — this is a production addition beyond the hackathon MVP, justified once query volume and corpus size make the extra latency (~100–200ms) worth the precision gain.

### 7.6 Prompt Construction

Retrieved chunks are assembled in a fixed template: system instructions → retrieved context (each chunk prefixed with its document name and page number) → conversation history (RFI chat only) → user question. Context is capped at a token budget (e.g., 8k tokens of retrieved context) to control cost and avoid diluting relevance with low-ranked chunks.

### 7.7 Hallucination Prevention

- Numeric clauses always deferred to the deterministic engine (§6.2/§6.6).
- The model is instructed to answer "insufficient information" rather than guess when retrieved context does not contain the answer, and this is evaluated explicitly in the eval set with negative (unanswerable) examples.

### 7.8 Citation Generation

Every answer's citations are derived mechanically from which chunk IDs were included in the prompt and referenced in the model's structured output — not free-text citations the model invents, which removes an entire class of citation-hallucination risk.

---

## 8. Database Design

### 8.1 ER Diagram

```mermaid
erDiagram
    PROJECTS ||--o{ DOCUMENTS : contains
    PROJECTS ||--o{ SUBMITTALS : contains
    PROJECTS ||--o{ RFIS : contains
    PROJECTS ||--o{ SHIPMENTS : contains
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : "split into"
    SUBMITTALS ||--o{ DEVIATIONS : produces
    USERS ||--o{ AUDIT_LOGS : performs
    PROJECTS ||--o{ USERS : "has members"

    PROJECTS {
        uuid id PK
        text name
        text status
        timestamptz created_at
    }
    DOCUMENTS {
        uuid id PK
        uuid project_id FK
        text filename
        int version
        boolean is_active
        text ingestion_status
    }
    DOCUMENT_CHUNKS {
        uuid id PK
        uuid document_id FK
        text chunk_text
        int page_number
        vector embedding
        boolean is_active
        uuid superseded_by
    }
    SUBMITTALS {
        uuid id PK
        uuid project_id FK
        uuid vendor_id
        text status
    }
    DEVIATIONS {
        uuid id PK
        uuid submittal_id FK
        text severity
        text detected_by
        text rule_version
    }
    RFIS {
        uuid id PK
        uuid project_id FK
        text question
        text response
        vector embedding
    }
    SHIPMENTS {
        uuid id PK
        uuid project_id FK
        text equipment_tag
        geography current_location
        text status
    }
    USERS {
        uuid id PK
        text email
        text role
    }
    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        text action
        text entity_type
        jsonb metadata
    }
```

### 8.2 Row-Level Security (production hardening)

Beyond the hackathon guide's baseline RLS policy, production adds:

```sql
-- Force RLS even for the table owner role (a common bypass vector)
ALTER TABLE submittals FORCE ROW LEVEL SECURITY;

-- Separate policies for read vs. write, so a compromised read-only
-- credential cannot be used to write cross-tenant data even if RLS
-- misconfiguration were somehow bypassed on one operation
CREATE POLICY tenant_read ON submittals FOR SELECT
    USING (project_id = current_setting('app.current_tenant_id')::uuid);
CREATE POLICY tenant_write ON submittals FOR INSERT, UPDATE, DELETE
    USING (project_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (project_id = current_setting('app.current_tenant_id')::uuid);
```

### 8.3 Partitioning & Scalability

`document_chunks` and `audit_logs` are the two tables expected to grow fastest. Both are range-partitioned by `project_id` hash once a single-node table exceeds ~50M rows, which keeps HNSW index rebuilds (on the rare occasions they are needed, e.g., changing `ef_construction`) scoped to a partition rather than the whole table.

### 8.4 Backup Strategy

Continuous WAL archiving with point-in-time recovery (15-minute RPO target); nightly full snapshot retained 30 days; monthly snapshot retained 1 year for audit-trail compliance requirements. Backup restore is tested quarterly against a staging environment, not assumed to work.

---

## 9. API Design

Representative endpoints (full OpenAPI spec generated automatically from FastAPI's Pydantic models — this table documents the contract, not an exhaustive list):

| Method | Endpoint | Auth | Request | Response | Rate limit |
|---|---|---|---|---|---|
| POST | `/projects/{id}/documents` | Bearer JWT | multipart file | `{document_id, status}` | 20/min/user |
| GET | `/projects/{id}/documents/{doc_id}` | Bearer JWT | — | `{id, filename, ingestion_status, page_count}` | 100/min/user |
| POST | `/projects/{id}/submittals` | Bearer JWT | `{document_id, spec_document_id}` | `{submittal_id, status: "queued"}` | 20/min/user |
| GET | `/projects/{id}/submittals/{id}/deviations` | Bearer JWT | — | `{deviations: [{clause, severity, detected_by, rationale}]}` | 100/min/user |
| POST | `/projects/{id}/rfi/query` | Bearer JWT | `{question}` | `{answer, citations, similar_rfis}` | 30/min/user |
| GET | `/projects/{id}/schedule/risk` | Bearer JWT | — | `{tasks: [{task_id, risk_score, top_factors}]}` | 60/min/user |
| POST | `/auth/refresh` | Refresh cookie + CSRF | — | `{access_token}` | 10/min/IP |

**Example request/response — Compliance findings:**

```json
POST /projects/proj_8841/submittals
{
  "document_id": "doc_2201",
  "spec_document_id": "doc_1190"
}

202 Accepted
{
  "submittal_id": "sub_5510",
  "status": "queued"
}
```

```json
GET /projects/proj_8841/submittals/sub_5510/deviations

200 OK
{
  "deviations": [
    {
      "clause": "Section 4.2.3 - Generator Clearance",
      "spec_value": ">= 900mm",
      "submitted_value": "750mm",
      "severity": "critical",
      "detected_by": "rule",
      "rationale": "Deterministic parser: submittal value 750mm fails constraint operator>=900mm.",
      "citations": [{"document_id": "doc_1190", "page_number": 42}]
    }
  ]
}
```

**Validation:** All request bodies validated against Pydantic models with explicit `Field` constraints (max lengths, enums for `severity`/`status`); validation failures return `422` with a field-level error map, never a generic 400.

**Errors:** Standardized error envelope `{ "error": { "code": "...", "message": "...", "request_id": "..." } }` across all services, so the frontend has one error-handling code path.

---

## 10. Background Jobs

### 10.1 Celery Task Inventory

| Task | Trigger | Retry policy | Timeout |
|---|---|---|---|
| `ingest_document` | Document upload | 5 retries, exponential backoff (2s, 4s, 8s, 16s, 32s) | 10 min |
| `run_compliance_check` | Submittal created | 3 retries | 3 min |
| `recompute_schedule_risk` | Schedule data updated + hourly cron | 3 retries | 5 min |
| `send_notification` | Deviation/risk threshold event | 5 retries, then DLQ | 30s |
| `refresh_dashboard_views` | 15-minute cron | 2 retries | 2 min |

### 10.2 Worker Topology

Separate Celery worker pools per queue (`ingestion`, `compliance`, `cv`, `notifications`) so a backlog in one (e.g., a burst of drawing uploads saturating the CV queue) cannot starve unrelated work (e.g., sending a critical-severity notification).

### 10.3 Dead Letter Queue

Tasks that exhaust their retry budget move to a DLQ table (`failed_jobs(id, task_name, payload, error, failed_at, resolved)`) surfaced in an internal admin view for manual triage — a permanently failing ingestion job (e.g., a corrupt PDF) should never silently vanish or infinitely retry.

---

## 11. Deployment Architecture

### 11.1 Local Development

```yaml
# docker-compose.yml (excerpt)
services:
  api:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://epc:epc@db:5432/epc_intel
      - REDIS_URL=redis://redis:6379/0
    depends_on: [db, redis]
    ports: ["8000:8000"]

  worker:
    build: ./backend
    command: celery -A app.worker worker -Q ingestion,compliance,notifications --concurrency=4
    depends_on: [db, redis]

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=epc_intel
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine

volumes:
  pgdata:
```

### 11.2 Production (Kubernetes — future state)

```yaml
# hpa.yaml (excerpt) - only introduced once traffic justifies it; see §15 roadmap
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 65 }
```

### 11.3 CI/CD (GitHub Actions)

```yaml
# .github/workflows/deploy.yml (excerpt)
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-fail-under=80
      - run: docker build -t epc-intel-api .
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploy to staging, run smoke tests, promote to prod on green"
```

### 11.4 Secrets Management

Production secrets (DB credentials, LLM API keys, JWT signing keys) live in a managed secrets store (AWS Secrets Manager / Vault), injected as environment variables at container start — never committed, never baked into container images.

---

## 12. Security

### 12.1 Authentication & Authorization

JWT (RS256, asymmetric so services can verify without holding the signing key) + RBAC with roles (`pm`, `qa_engineer`, `procurement_lead`, `commissioning_engineer`, `admin`) mapped to endpoint-level permission checks enforced in FastAPI dependency injection, not scattered ad hoc across handlers.

### 12.2 Encryption

TLS 1.3 in transit everywhere. At rest: managed-database encryption (AES-256) plus application-level encryption of specific highly sensitive fields (e.g., commercial pricing in procurement records) using envelope encryption via a KMS, so a database-level compromise alone does not expose those fields.

### 12.3 API Security (OWASP alignment)

Input validation via Pydantic (§9), parameterized queries only (no string-built SQL), rate limiting per endpoint, and dependency scanning (`pip-audit` / `npm audit`) in CI as a merge-blocking check.

### 12.4 LLM Security

- **Prompt injection:** Document content is never concatenated into the system prompt with instruction-following privileges — it is passed as clearly delimited "retrieved context," and the system prompt explicitly instructs the model to treat document content as data, not instructions.
- **PII protection:** A PII-detection pass runs on ingested documents (names, emails, national ID patterns) and flags/redacts before any content is sent to a third-party hosted LLM, with the self-hosted fallback model (§6.1) as the path for content that must not leave the tenant's environment.

### 12.5 Row-Level Security

Covered in depth in §8.2 and the hackathon guide §7 — the single most important control in this section, since it is what makes a bug in application code unable to leak data.

---

## 13. Performance Optimization

### 13.1 Caching Strategy

| What | Where | TTL | Invalidation |
|---|---|---|---|
| RFI answer cache (similarity > 0.85) | Redis | 24h | Manual on document re-ingestion |
| Compliance clause-retrieval results | Redis | 1h | On new document version |
| Dashboard aggregates | Materialized view | 15 min (cron refresh) | Scheduled refresh |
| JWT revocation list | Redis | Token TTL | On logout/revoke |

### 13.2 Batch & Async Processing

Embedding generation, CV inference, and OCR fallback are always async (Celery), never inline in the request path — the request path only ever creates a job and returns `202`.

### 13.3 Database Optimization

Composite indexes on every `(project_id, <hot column>)` pattern (§8.2); connection pooling via PgBouncer in transaction-pooling mode to keep Postgres connection counts bounded as API pod count scales horizontally.

### 13.4 Scaling Triggers (when to add complexity)

| Signal | Action |
|---|---|
| `document_chunks` exceeds ~50M rows or HNSW query p95 exceeds SLA | Consider a dedicated vector DB or partition the table (§8.3) |
| Sustained API CPU utilization > 65% | Kubernetes HPA scales API pod count (§11.2) |
| Celery queue depth sustained > threshold for > 10 min | Add worker replicas for that specific queue |
| LLM cost per project exceeds budget threshold | Tighten top-k retrieval, raise cache-hit target, evaluate self-hosted model for that workload |

---

## 14. Failure Recovery

| Failure | Detection | Recovery |
|---|---|---|
| LLM API outage/rate-limit | Circuit breaker trips after N consecutive failures | Route to self-hosted fallback model (§6.1); if both unavailable, queue the compliance job for retry rather than failing the user request |
| Celery worker crash mid-task | Task visibility timeout exceeded | Task redelivered to another worker; idempotency keys on ingestion tasks prevent duplicate processing |
| Database primary failure | Health check / managed-service failover | Automatic failover to read replica promoted to primary (managed Postgres); application retries with backoff during failover window |
| CV GPU node pool saturated | Queue-depth alert | Jobs queue rather than degrade silently to a lower-quality CPU path (§6.3) |
| Redis unavailable | Connection errors on cache/broker calls | Cache layer fails open (skip cache, hit DB/LLM directly) rather than failing the request; Celery broker outage pages on-call, since job dispatch genuinely cannot proceed |

**Circuit breaker example (conceptual):**

```python
class LLMCircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failures = 0
        self.state = "closed"
        self.opened_at = None

    def call(self, fn, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.opened_at > self.reset_timeout:
                self.state = "half_open"
            else:
                raise CircuitOpenError("LLM circuit open, routing to fallback")
        try:
            result = fn(*args, **kwargs)
            self.failures = 0
            self.state = "closed"
            return result
        except LLMProviderError:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.state = "open"
                self.opened_at = time.time()
            raise
```

---

## 15. Development Roadmap

This is the **post-hackathon production roadmap**, distinct from the 48-hour hackathon sprint plan. It assumes the hackathon MVP (Compliance, RFI, Drawing Review) is the starting codebase.

**Week 1 — Hardening the core:** Production RLS audit (force RLS, read/write policy split); confidence-scored human review queue for compliance findings; PII detection pass on ingestion; move CV inference to a GPU node pool; expand the evaluation set from 100 to 500 labeled clauses.

**Week 2 — Background processing & reliability:** Introduce Celery + Redis with per-queue worker pools; Dead Letter Queue and admin triage view; circuit breaker around the LLM gateway; structured logging and request tracing across all services.

**Week 3 — Remaining modules to production quality:** Build the real Schedule Risk model (baseline → logistic regression → LightGBM with SHAP) on real historical data if available; build the Procurement/Supply Chain module against a real carrier-tracking API; begin licensing negotiation for TIA-942/BICSI commissioning content.

**Week 4 — Deployment & observability:** Kubernetes manifests and staged rollout (staging → canary → full); Prometheus/Grafana dashboards for the SLOs defined in §13.4; load testing (§16.4) against production-scale synthetic data (hundreds of thousands of chunks); quarterly backup-restore drill scheduled.

---

## 16. Testing Strategy

### 16.1 Unit Testing
Every module in §5 has unit tests for its core logic in isolation (rule-engine constraint parsing, RRF fusion math, RLS policy SQL via a test database role) — target 80%+ coverage on business logic, not on framework glue code.

### 16.2 Integration Testing
End-to-end ingestion → chunking → embedding → retrieval pipeline tested against a fixed sample document set on every merge to `main`.

### 16.3 API Testing
Contract tests generated from the OpenAPI spec (§9) run against a staging deployment before promotion to production.

### 16.4 Load Testing
Synthetic load (e.g., via Locust) simulating the target production scale (15,000–40,000 line items, hundreds of concurrent submittal reviews) run quarterly and after any change to the retrieval or compliance pipeline, tracking p50/p95/p99 latency against the SLOs in §13.4.

### 16.5 AI Evaluation
The 100-item (hackathon) → 500-item (production) labeled evaluation set (§15) is the regression gate for any prompt, model, or rule-engine change — a change that regresses precision/recall on this set blocks merge, the same way a failing unit test would.

### 16.6 Regression Testing
Full evaluation-set re-run plus the CV mAP benchmark re-run on every model or prompt version bump, with results tracked over time (not just pass/fail) so a slow degradation is caught before it becomes a step-function failure.

---

## 17. Cost Estimation

Indicative monthly costs at a "one active hyperscale project" scale (order-of-magnitude, not a quote):

| Category | Item | Est. monthly cost (USD) |
|---|---|---|
| Compute | API + worker pods (Kubernetes, mixed CPU) | $400–800 |
| Compute | GPU node pool (CV inference, on-demand/spot mix) | $300–600 |
| Database | Managed PostgreSQL (pgvector-enabled, appropriately sized) | $250–500 |
| Cache/broker | Managed Redis | $50–150 |
| Object storage | S3-equivalent (document + drawing storage) | $20–60 |
| LLM inference | Compliance + RFI chat (with caching, top-k capping) | $300–1,200 depending on query volume |
| Monitoring | Self-hosted Prometheus/Grafana (compute only, no license) | $50–100 |
| **Total (indicative)** | | **~$1,400–3,400/month per active project** |

**Cost levers:** cache-hit rate on RFI queries (§13.1), top-k retrieval size (§7.6), and self-hosted-model fallback usage (§6.1) are the three largest controllable cost drivers — each is instrumented with a dedicated metric so cost regressions are visible before the invoice arrives, not after.

---

## 18. Future Enhancements

### 18.1 Enterprise Deployment
Multi-region deployment for data-residency-sensitive clients; SSO (SAML/OIDC) integration for enterprise identity providers; per-tenant configurable retention policies for audit logs.

### 18.2 Knowledge Graph
A knowledge graph (equipment ↔ spec clause ↔ submittal ↔ RFI relationships) is a plausible future enhancement **once** the relational + vector model demonstrably cannot answer relationship-traversal queries users are actually asking for (e.g., "show me every RFI touching any clause this changed spec revision affects") — it is explicitly not included in the initial production build, consistent with the "no unjustified complexity" principle in §2.1.

### 18.3 Multi-Agent System
A single ReAct agent (§6, hackathon guide §4) is sufficient while the task surface is "answer a compliance question, draft an RFI." A multi-agent architecture is justified only if and when distinct, genuinely parallelizable specialist roles emerge with low inter-agent coordination need (e.g., a dedicated Commissioning-test-sequencing agent operating on an entirely separate document set) — until then, additional agents add coordination failure modes (as the strict architecture evaluation of the hackathon design correctly warned) without adding capability a single agent with more tools couldn't provide.

### 18.4 Predictive Analytics
Cost-overrun prediction alongside schedule-risk prediction, using the same baseline-then-beat-it methodology as §5.9/§15.

### 18.5 BIM Integration
Ingesting BIM model metadata (IFC format) to cross-reference drawing-review CV findings (§6.3) against the 3D model's own clearance data as a second, independent verification signal.

### 18.6 IoT Integration
Real-time sensor feeds (temperature, humidity, power quality) during commissioning, correlated against the Commissioning Intelligence module's expected test values — a natural extension of §5.11 once the core commissioning workflow is validated with human-entered data.

---

## 19. Appendix

### 19.1 Folder Structure

```
epc-intel/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI routers, one per module in §5
│   │   ├── services/             # Business logic, framework-agnostic
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── ai/
│   │   │   ├── compliance/       # Dual-layer engine (§6.1, §6.2)
│   │   │   ├── rag/              # Chunking, embedding, hybrid search (§7)
│   │   │   ├── cv/               # YOLO11 + Eigen-CAM pipeline (§6.3)
│   │   │   └── schedule_risk/    # Baseline + LightGBM models (§5.9)
│   │   ├── worker/               # Celery tasks (§10)
│   │   └── core/                 # Config, security, RLS session middleware
│   ├── migrations/                # Alembic
│   └── tests/
├── frontend/
│   ├── app/                       # Next.js App Router pages, one per module
│   └── components/
├── infra/
│   ├── docker-compose.yml
│   ├── k8s/
│   └── github-actions/
├── eval/
│   ├── compliance_eval_set.json   # Labeled evaluation set (§16.5)
│   └── run_eval.py
└── docs/
```

### 19.2 Naming Conventions

- Database tables: `snake_case`, plural (`documents`, `deviations`).
- API routes: `kebab-case` path segments, plural resource nouns (`/rfi-queries`, not `/rfiQuery`).
- Celery tasks: `verb_noun` (`ingest_document`, `recompute_schedule_risk`).
- Environment variables: `UPPER_SNAKE_CASE`, prefixed by service (`COMPLIANCE_LLM_MODEL`, `RAG_TOP_K`).

### 19.3 Coding Standards

Python: `ruff` + `black` enforced in pre-commit and CI; type hints required on all public function signatures; no bare `except:` clauses. TypeScript: `eslint` + `prettier`; `strict` mode enabled in `tsconfig.json`.

### 19.4 Key Environment Variables

```
DATABASE_URL=postgresql://user:pass@host:5432/epc_intel
REDIS_URL=redis://host:6379/0
LLM_PRIMARY_PROVIDER=anthropic
LLM_FALLBACK_PROVIDER=self_hosted_llama3_70b
RAG_TOP_K=8
RAG_CACHE_SIMILARITY_THRESHOLD=0.85
JWT_SIGNING_KEY_PATH=/secrets/jwt_rs256_private.pem
S3_BUCKET=epc-intel-documents
CV_MODEL=yolo11
CV_GPU_NODE_POOL=true
```

### 19.5 Configuration Files

Standard `.env.example` committed (no real secrets); `pyproject.toml` for Python tooling config; `docker-compose.override.yml.example` for local developer customization without touching the tracked compose file.

---

*This document is the production-scale companion to the 48-hour hackathon MVP guide. Where the two disagree on scope (Celery/Redis, Kubernetes, multi-service decomposition), the hackathon guide governs what gets built in 48 hours; this document governs what the team builds next.*
