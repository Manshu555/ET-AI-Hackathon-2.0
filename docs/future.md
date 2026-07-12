# EPC-Intel — Hackathon Judge Panel Evaluation

## Final Verdict & Improvement Plan

**Date:** July 12, 2026  
**Event:** ET AI Hackathon 2026 — Grand Finale  
**Team Solution:** EPC-Intel — AI-Powered EPC Intelligence Platform  
**Problem Statement:** #4 — Data Centre EPC Intelligence  

---

## PANEL COMPOSITION

| Judge | Affiliation |
|---|---|
| Principal AI Architect | Google DeepMind |
| Distinguished Engineer | Microsoft |
| AWS Principal Solutions Architect | Amazon Web Services |
| NVIDIA AI Systems Engineer | NVIDIA |
| Enterprise EPC Domain Expert | Construction & Infrastructure |
| VC Technical Due Diligence Reviewer | Venture Capital |
| Professor in ML Systems | Academia |

---

## 1. PROBLEM UNDERSTANDING — Score: 5/10

### What's covered:
- Document ingestion pipeline (PDF → chunks → embeddings → pgvector) ✓
- Compliance deviation detection (dual-layer: rule + LLM) ✓
- RFI chat assistant with RAG ✓
- Authentication (JWT + bcrypt) ✓
- Multi-tenant isolation concept (RLS via project_id) ✓

### What's missing:
- **Schedule Risk Intelligence** — required by the problem statement, **not implemented at all**. No models, no module, no UI page, no API endpoint. The `ml/` directory is empty.
- **Procurement Intelligence** — required, not implemented. No shipment tracking, no vendor lead-time analysis.
- **Commissioning Intelligence** — required, not implemented. No test sequence management.
- **Computer Vision / Drawing Review** — mentioned in the architecture doc as a key differentiator (YOLO11 + Eigen-CAM), completely absent from the codebase.
- **Notification Engine** — not implemented.
- **Audit Logging** — not implemented. Critical for EPC compliance.
- **Executive Dashboard** — the dashboard page exists but shows **hardcoded fake data** (14, 5, 32), not live aggregations.

### Verdict:
The team implemented approximately **3 out of 8+ required modules**. The solution covers ingestion, compliance, and RFI — which are the core modules — but the problem statement explicitly requires schedule risk, procurement tracking, and commissioning. These are not "nice-to-haves"; they are in the problem statement.

> **"Insufficient evidence"** that the team understood the full scope of the problem. They built deeply on a narrow slice rather than covering the breadth.

---

## 2. ARCHITECTURE — Score: 10/20

### Strengths:
- Clean modular FastAPI structure: `Router → Service → Model → Schema`
- Separation of concerns between auth, documents, compliance, RFI
- pgvector for combined relational + vector storage — avoids operational complexity of a second database
- Docker Compose for infrastructure (Postgres + MinIO)
- Alembic for migrations (setup exists, even if not fully functional)
- CORS middleware properly configured

### Weaknesses:

**Critical:**
1. **S3Client was crashing the entire server at import time.** The `boto3.client()` constructor was called at module load. If MinIO was down, FastAPI couldn't even start. Fixed mid-hackathon, but this indicates a lack of resilience testing.
2. **No database actually runs.** PostgreSQL is required but never started. The backend runs in a permanent "fallback mode" where every DB operation fails silently. **This means no data actually persists.** No user registration works. No document upload works end-to-end. No compliance check can actually run.
3. **`documents/router.py` imports `s3_client` at module level**, which force-connects to MinIO on import. If MinIO is down, the router import fails and the entire app crashes.
4. **Celery worker cannot run** — Redis is not started. Document ingestion `process_document.delay()` would fail.

**Major:**
5. **No error handling middleware.** No global exception handler. Unhandled exceptions return raw 500 tracebacks to the client.
6. **No request validation beyond Pydantic.** No rate limiting. No request-size limits beyond FastAPI defaults.
7. **No health check for dependencies.** The `/health` endpoint returns `{"status": "ok"}` even when Postgres, Redis, and MinIO are all down. This is a lie.
8. **Login page doesn't actually authenticate.** It's a `<Link>` tag that navigates to `/dashboard` with no API call.

**Minor:**
9. Docker Compose missing Redis service (required by Celery).
10. No `.env.example` file. Credentials hardcoded as defaults in `config.py`.
11. No Dockerfile for the backend.

### Architecture Diagram vs. Reality:
The docs contain a beautiful 13-service Kubernetes architecture with CDN, API Gateway, HPA, Prometheus, Grafana, and 8 Celery queues. The actual implementation is a single FastAPI process with 3 routers that cannot connect to its own database. **The gap between the documented architecture and the built system is enormous.** Judges will notice this immediately.

---

## 3. AI ENGINEERING — Score: 5/15

### What exists:
- Gemini 2.0 Flash integration for RFI chat ✓
- Gemini 2.0 Flash integration for compliance semantic reading ✓
- Sentence-transformers embedding (all-MiniLM-L6-v2, 384 dims) ✓
- Deterministic numeric rule extraction (regex-based) ✓

### Criticisms:

1. **The RFI chat is just a raw LLM call with no RAG context.** Because Postgres is never running, the vector search never executes. The `context_str` is always `""`. The chat is a bare `gemini-2.0-flash` call with a system prompt — **this is not RAG, this is a chatbot with a construction-themed system prompt.** Any competing team running ChatGPT with a system prompt achieves the same result.

2. **No evaluation of AI outputs.** Zero metrics. No precision/recall measurement. No comparison against a baseline. No labeled test set. The architecture doc (§9.1) mentions a "100-item labeled evaluation set" — it does not exist in the codebase.

3. **No prompt engineering sophistication.** The compliance prompt is:
   ```
   "Does the submittal deviate from the specification? Reply with JSON..."
   ```
   This is a zero-shot prompt with no few-shot examples, no chain-of-thought, no structured output enforcement (e.g., Gemini's JSON mode), no temperature tuning.

4. **`google.generativeai` was deprecated** during the hackathon and had to be migrated to `google.genai` mid-demo. This indicates the team did not test their SDK dependencies before arriving.

5. **No fallback model.** If the Gemini API key is rate-limited (which it was), the entire AI layer returns an error string to the user. No local model fallback, no retry logic, no queue.

6. **The dual-layer compliance check is architecturally sound** (rule engine + LLM, rule wins on numeric disagreement) — but it has never actually been executed because the database is not running.

### Challenge: "Why does this need AI?"
- **Compliance semantic reading:** Justified — natural-language spec clauses cannot be rule-parsed.
- **RFI chat:** Justified in concept, but current implementation is just a generic chatbot.
- **Numeric rule extraction:** Correctly implemented as deterministic regex, not AI. Good.

---

## 4. DATA ENGINEERING — Score: 2/10

1. **No actual data flows through the system.** PostgreSQL is not running. MinIO is not running. Redis is not running. The ingestion pipeline (`tasks.py`) has never been executed.

2. **Chunking strategy is naive.** `chunk_text()` splits on whitespace with a fixed window of 500 words and 100-word overlap. This is explicitly called out in the architecture doc (§7.1) as the wrong approach — "never a fixed token-count splitter, which risks bisecting a table row." The implementation does exactly what the architecture doc says not to do.

3. **No metadata extraction.** Chunks do not have `section_path`. `page_number` is hardcoded to `1` for all chunks ("Simplified for hackathon"). This means the citation system cannot reference the correct page.

4. **No document versioning logic.** The `is_active` / `superseded_by` fields described in the architecture doc are absent from the `DocumentChunk` model.

5. **No data quality checks.** No validation of PDF content. No garbled-text detection. No OCR fallback.

6. **Synthetic data:** None. No seed data. No test fixtures. The dashboard shows hardcoded numbers.

---

## 5. MACHINE LEARNING — Score: 1/10

1. **The `ml/` directory is empty.** No training data, no feature engineering, no model, no evaluation, no baseline.

2. **Schedule Risk Model** — described extensively in the architecture doc (§5.9: "naive baseline → logistic regression → LightGBM, SHAP values for explainability") — does not exist in any form.

3. **No ML pipeline of any kind.** No training scripts, no notebooks, no experiment tracking, no model registry.

4. **The embedding model (all-MiniLM-L6-v2) is used correctly** but is a 384-dimension model while the architecture doc specifies `bge-large-en-v1.5` (1024 dimensions). This is a downgrade that was not documented or justified.

5. **No evaluation metrics anywhere.** No accuracy, no precision, no recall, no F1, no mAP. Insufficient evidence that any component was evaluated.

---

## 6. RAG SYSTEM — Score: 2/10

1. **RAG is architecturally present but functionally dead.** The code for vector search exists in `rfi/service.py` — `embedding <=> :embedding` with cosine distance on pgvector — but since PostgreSQL never runs, it has never been tested.

2. **No hybrid retrieval.** The architecture doc specifies BM25 + pgvector + RRF fusion. The implementation only has dense vector search (cosine similarity). No full-text search. No RRF.

3. **No reranking.** No cross-encoder. No `bge-reranker`.

4. **No citation quality.** The `citations` field stores raw chunk UUIDs as a JSON string. There is no document name, no page number, no excerpt in the citation output. The frontend does not render citations.

5. **No context management.** No conversation history sent to the LLM. Each message is independent.

6. **No hallucination handling** beyond the architecture doc's description. No "insufficient information" response logic. No confidence scoring.

7. **No caching.** The architecture doc describes a cosine-similarity cache (>0.85 threshold) — not implemented.

8. **Embedding model mismatch:** Implementation uses `all-MiniLM-L6-v2` (384d), architecture doc says `bge-large-en-v1.5` (1024d). Not justified.

---

## 7. USER EXPERIENCE — Score: 4/10

### Login Page:
- Visually clean, glassmorphism aesthetic. Good first impression.
- **Does not actually authenticate.** The "Sign In" button is a `<Link href="/dashboard">` — no API call, no credentials validation. Any judge who types random credentials will get in. Red flag.

### Dashboard:
- Clean 3-card KPI layout. Visual hierarchy is acceptable.
- **All data is hardcoded:** "14 Open Deviations", "5 Pending RFIs", "32 Approved Submittals". These numbers never change. "Recent Activity" is static HTML. This will be immediately obvious to judges.
- No project selector. No date range filter. No drill-down.

### Upload Page:
- Drag-and-drop UI is clean.
- **Upload button shows an `alert()` popup**: "In a real app, this would upload to FastAPI & MinIO!" This is demo-breaking. A judge clicking "Upload & Process" gets a JavaScript alert box admitting the feature doesn't work.

### Compliance Review:
- Table layout with severity badges (Critical/Minor) is appropriate for the domain.
- **Hardcoded data** — only 2 static deviations rendered from a constant array.
- Override/Reject buttons have no `onClick` handlers. They do nothing.

### RFI Chat:
- Chat UI is functional — real-time message exchange with the backend.
- **This is the only page with a live backend connection.** It is the strongest demo asset.
- No loading indicator while waiting for AI response.
- No markdown rendering of AI responses.
- No citation display.
- Session management is hardcoded to `"demo-session-123"`.

### Overall UX Verdict:
A real EPC engineer would open this and see hardcoded data on 3 of 4 pages, a non-functional upload, and a chat that works but provides no citations. **The only live feature is the RFI chat, and it is a generic chatbot without project context** (because the database is not running).

---

## 8. IMPLEMENTATION FEASIBILITY — Score: 4/10

### 48-hour hackathon with 4 developers:

**What's realistic:**
- Auth + JWT: Feasible ✓ (implemented)
- Document ingestion pipeline: Feasible (implemented but untested)
- One AI feature (compliance or RFI chat): Feasible ✓
- Basic frontend with 4 pages: Feasible ✓
- Docker Compose for infra: Feasible ✓

**What's over-engineered for 48 hours:**
- The 50+ page production architecture blueprint in docs/. This document describes Kubernetes, HPA, Prometheus, Grafana, SHAP, YOLO11, Eigen-CAM, cross-encoder reranking, envelope encryption, and a 4-week roadmap. Zero of this is built. The time spent writing this document could have been spent getting Postgres and MinIO actually running.

**What should have been cut:**
- Celery + Redis dependency — unnecessary for a hackathon. Synchronous document processing would have been fine.
- S3/MinIO dependency — local filesystem storage would have worked for a demo.
- Multiple complex SQLAlchemy models that are never populated with data.

**What's missing:**
- A working database. This is the #1 critical gap.
- Seed data / fixtures so the demo has realistic content.
- End-to-end testing of any single flow.

---

## 9. INNOVATION — Score: 3/10

### What every competing team already has:
- RAG with a vector database ✓
- LLM chat interface ✓
- PDF ingestion ✓
- FastAPI + Next.js stack ✓

### What would be genuinely innovative:
- **Dual-layer compliance check (rule engine + LLM with reconciliation)** — this IS a good idea and a genuine differentiator. But it has never actually executed.
- **Deterministic numeric extraction that overrides LLM on disagreement** — architecturally sound and defensible. Not demonstrated.
- **Schedule risk prediction with SHAP explainability** — described but not built.

### Verdict:
The innovation exists **in the documentation, not in the code**. The architecture doc is genuinely well-thought-out and would score highly if it were built. But a hackathon is judged on what runs, not what is described.

---

## 10. BUSINESS VALUE — Score: 2/5

- **Would an EPC company buy this?** Not in its current state. The only working feature (RFI chat) is a generic Gemini chatbot with no project-specific context.
- **Would engineers trust it?** The compliance page shows hardcoded data with no source citations. Engineers would not trust unattributed AI findings.
- **Deployment complexity:** Cannot deploy as-is. Requires PostgreSQL, MinIO, Redis — none are running.
- **ROI:** Unclear. No metrics on time saved, errors caught, or cost reduction.
- **Integration effort:** No API documentation beyond auto-generated OpenAPI. No webhooks. No SSO.

---

## UI REVIEW (Per Screen)

| Screen | Purpose | Clarity | Live Data? | AI Usefulness | Trustworthy? | 30s Comprehension? |
|---|---|---|---|---|---|---|
| Login | Auth gate | Good | N/A | N/A | ❌ No real auth | ✅ Yes |
| Dashboard | KPI overview | Good | ❌ Hardcoded | N/A | ❌ Fake data | ✅ Yes |
| Upload | Doc ingestion | Good | ❌ alert() | N/A | ❌ Broken | ✅ Yes |
| Compliance | Deviation review | Good | ❌ Hardcoded | ❌ Not connected | ❌ No citations | ✅ Yes |
| RFI Chat | AI Q&A | Good | ✅ Live | ⚠️ Generic chatbot | ⚠️ No citations | ✅ Yes |

---

## ARCHITECTURE REVIEW (Detailed)

| Aspect | Assessment |
|---|---|
| Component Diagram | Exists in docs — extremely comprehensive. Not reflected in code. |
| Data Flow | Designed but never executed end-to-end. |
| Sequence Diagram | Mermaid diagrams in architecture doc are excellent. |
| Deployment Diagram | K8s + HPA described. Reality is a single uvicorn process. |
| Database Design | ER diagram is well-designed. Tables defined in SQLAlchemy but never created in Postgres. |
| API Design | 8 endpoints registered. Only `/health` and `/rfi/chat` actually work. |
| Folder Structure | Clean and modular. Best aspect of the implementation. |
| Security | JWT + bcrypt implemented. No CSRF. No rate limiting. Login is fake. |
| Monitoring | None. No logging aggregation, no metrics, no tracing. |
| CI/CD | Described in docs. Not implemented. No GitHub Actions workflow exists. |
| Failure Handling | Improved mid-hackathon with try/except wrappers. Functional but reactive. |

---

## DEMO REVIEW (10-minute demo)

### Recommended Demo Sequence:
1. (0:00–1:00) Problem statement + architecture overview
2. (1:00–2:00) Login → Dashboard (skip quickly, don't linger on static data)
3. (2:00–4:00) **RFI Chat** — this is your strongest asset. Ask 2-3 engineering questions.
4. (4:00–6:00) Compliance Review — explain the dual-layer concept, show the UI
5. (6:00–8:00) Upload page — explain the ingestion pipeline architecture
6. (8:00–10:00) Architecture deep-dive + future roadmap

### Risks of Failure:
- **HIGH RISK:** Gemini API key quota exhaustion (already happened). If this fails during demo, the only live feature dies.
- **HIGH RISK:** Judge clicks "Upload & Process" and gets a JavaScript alert saying it's fake.
- **MEDIUM RISK:** Judge enters wrong credentials on login and still gets in.
- **LOW RISK:** Backend crashes if a dependency import fails.

### Strongest Demo: RFI Chat (only live AI feature)
### Weakest Demo: Upload Page (admits it doesn't work via alert())

---

## 30 HARDEST QUESTIONS JUDGES WILL ASK

### Architecture
1. Your architecture doc shows 13 microservices. How many are actually running?
2. Why can't your backend connect to its own database?
3. Why did you choose Celery + Redis when you could have processed documents synchronously for a hackathon?
4. How does your system handle concurrent users if you have no connection pooling configured?
5. Why is there no Dockerfile in your backend directory?

### AI
6. Your RFI chat returned an error when we tested it. What's your fallback strategy?
7. You claim dual-layer compliance checking. Can you show us one actual compliance check running live?
8. What's your retrieval accuracy? What's your precision/recall?
9. Why are you using all-MiniLM-L6-v2 (384d) when your architecture doc specifies bge-large-en-v1.5 (1024d)?
10. How do you handle hallucinations in the RFI chat?

### ML
11. Your `ml/` directory is empty. Where is the schedule risk model described in your architecture?
12. What training data did you use?
13. What's your baseline comparison?
14. How would you evaluate the compliance engine's accuracy?
15. Show us SHAP values for one prediction.

### Security
16. Your login page doesn't actually validate credentials. Is this intentional?
17. How do you prevent prompt injection through uploaded documents?
18. Your API has no rate limiting. What happens under load?
19. The GEMINI_API_KEY is stored in plaintext in `.env`. What's your secrets management strategy?
20. How does RLS work if the database is never running?

### Business
21. What's the total cost per compliance check (LLM tokens + compute)?
22. How long does a full document ingestion take for a 500-page spec?
23. What's your pricing model?
24. How do you handle regulatory requirements (ISO 19650, BIM standards)?
25. Which EPC companies have you validated this with?

### Deployment & Scaling
26. How would you deploy this to production tomorrow?
27. What's your disaster recovery strategy?
28. How do you handle document updates / version control?
29. What happens when a Celery worker crashes mid-ingestion?
30. How would you scale to 100 concurrent users?

---

## RED FLAGS

| Red Flag | Evidence |
|---|---|
| 🚩 Marketing language | Architecture doc describes features not built (YOLO11, SHAP, Kafka, Kubernetes) |
| 🚩 Unsupported claims | "AI flagged a Major deviation" — this is hardcoded HTML, not an AI output |
| 🚩 Buzzwords | "Glassmorphism", "Deterministic backstop", "Reciprocal Rank Fusion" — described but not implemented |
| 🚩 Fake AI | Dashboard numbers are static. Compliance deviations are hardcoded. Only RFI chat is live. |
| 🚩 Unrealistic assumptions | Architecture doc assumes Kubernetes, GPU node pools, managed Postgres — none available |
| 🚩 Missing evaluation | Zero metrics. No eval set. No baseline comparison. No A/B test. |
| 🚩 Missing evidence | "Reduction in manual cross-referencing hours" — no measurement, no user study |
| 🚩 Overengineering | 50-page production architecture blueprint for a 48-hour hackathon with no working database |
| 🚩 Non-functional demo | Upload page shows `alert("In a real app...")` — fatal during a live demo |
| 🚩 API key exhaustion | Gemini 429 error during testing — no retry/fallback strategy |

---

## WINNING POTENTIAL

### Compared to an ideal first-place submission:

A first-place team would have:
- A fully working end-to-end demo with real data flowing through the system
- At least 2 AI features working live (not just one chatbot)
- Measurable results (X% accuracy, Y seconds saved)
- A polished demo with zero dead-end screens
- Something genuinely novel that no other team built

### Realistic placement: **Top 25 — Average**

**Reasoning:**
- The architecture documentation is graduate-thesis quality and shows genuine domain understanding.
- The code quality and folder structure are professional-grade.
- But only 1 out of 4 UI pages works live, the database never connects, and the only AI feature is a generic Gemini chatbot.
- Competing teams running a basic RAG chatbot with a working database and real document ingestion will outperform this solution in a live demo.

---

## FINAL SCORE

| Criterion | Score | Notes |
|---|---|---|
| Problem Understanding | **5/10** | 3 of 8+ modules implemented. Missing schedule, procurement, commissioning. |
| Architecture | **10/20** | Excellent design docs. Poor execution. No working database. |
| AI Engineering | **5/15** | Gemini integration works. No RAG context. No evaluation. |
| Data Engineering | **2/10** | Pipeline code exists but never executed. Naive chunking. |
| Machine Learning | **1/10** | Empty ml/ directory. No models. No training. |
| RAG System | **2/10** | Code present but pgvector never runs. No hybrid search. |
| User Experience | **4/10** | Clean design. 4/5 pages show hardcoded/fake data. |
| Implementation Feasibility | **4/10** | Overengineered docs, under-built code. |
| Innovation | **3/10** | Dual-layer compliance is novel. Not demonstrated. |
| Business Value | **2/5** | Cannot demo value. No metrics. |
| **TOTAL** | **38/100** | |

---

## FINAL VERDICT

### 1. BIGGEST STRENGTHS (Top 10)

1. **Architecture documentation is exceptional.** The production blueprint is one of the most thorough, honest, and technically defensible architecture docs we've reviewed. It explicitly justifies every technology choice against alternatives and acknowledges trade-offs.
2. **Dual-layer compliance design (rule + LLM, rule wins on numeric).** This is a genuinely novel and defensible approach that no competing team is likely to have.
3. **Clean code organization.** The `Router → Service → Model → Schema` pattern is consistent across all modules.
4. **FastAPI + Next.js stack** is well-chosen for this use case.
5. **pgvector for combined relational + vector** avoids a second data store — pragmatic decision.
6. **Frontend glassmorphism design** creates a professional first impression.
7. **The RFI chat actually connects to a real LLM** and returns dynamic responses.
8. **Deterministic numeric extraction** correctly avoids LLM for quantitative checks.
9. **JWT + bcrypt authentication** is properly implemented on the backend.
10. **Graceful degradation** was added mid-hackathon (lazy S3 client, DB fallback) — shows adaptability.

### 2. BIGGEST WEAKNESSES (Top 10)

1. **No working database.** PostgreSQL is never started. Every DB-dependent feature silently fails.
2. **Only 1 of 4 pages has live data.** Dashboard, Upload, Compliance are all fake/hardcoded.
3. **Upload page shows a JavaScript `alert()` admitting it's not real.** Demo-fatal.
4. **Login doesn't authenticate.** It's just a link to the dashboard.
5. **No evaluation metrics for any AI component.** Zero evidence of effectiveness.
6. **The `ml/` directory is empty.** Schedule risk — a required feature — is entirely absent.
7. **Massive gap between architecture docs and implementation.** Docs describe 13 services; 3 routers exist.
8. **RAG is non-functional.** Vector search code exists but never executes.
9. **API key quota exhausted during testing.** No fallback or retry strategy.
10. **No seed data / fixtures.** A judge cannot see any realistic scenario play out.

### 3. TOP 10 IMPROVEMENTS REQUIRED BEFORE FINALS

1. **Get PostgreSQL running.** Use SQLite as a local fallback if Docker is unavailable. This unblocks every feature.
2. **Remove the `alert()` from the upload page.** Either make it work or replace it with a loading simulation.
3. **Make login functional.** Add a demo credential that actually validates against the backend.
4. **Pre-populate the database with realistic EPC data** — 5 specifications, 3 submittals, 10 deviations, 3 RFIs.
5. **Connect the compliance page to the backend API** so it displays real AI-generated deviations.
6. **Connect the dashboard to the backend** to show real aggregated counts.
7. **Add a loading spinner and markdown rendering to the RFI chat.**
8. **Create at least a basic schedule risk heuristic** (even rules-based) so the module isn't completely missing.
9. **Add 3 few-shot examples to the compliance prompt** to improve accuracy.
10. **Prepare a backup plan for API key quota** — have a second key or a local model ready.

### 4. IF YOU WERE A JUDGE, WOULD YOU VOTE FOR THIS SOLUTION TO WIN?

**No.**

The architecture documentation alone demonstrates that this team has a deeper understanding of the EPC domain and AI system design than most competitors. The dual-layer compliance concept is genuinely innovative. The code quality is professional.

But hackathons are judged on what works in a live demo, not on what is described in a document. When a judge clicks through this application, they will see:
- A login that doesn't authenticate
- A dashboard with hardcoded numbers
- An upload button that shows a JavaScript alert
- A compliance table with static data
- A chatbot that works but has no project-specific context

**A competing team with a worse architecture doc but a working database, real document ingestion, and a RAG chatbot that cites actual documents will win.** Running code beats beautiful documentation every time.

The team's fatal mistake was spending too much time on architecture documentation and not enough time on getting the core infrastructure (PostgreSQL, MinIO) running. A 48-hour hackathon demands ruthless prioritization of what demos well, not what scales well.

**Recommendation:** This team has the strongest architectural thinking of any team we're likely to see. If they can get the database running, seed it with data, and connect the frontend pages to live APIs in the next session, they could realistically jump from Average to **Top 10**. The foundation is there. The execution gap is what's holding them back.

---

> *"The best architecture in the world is worthless if it can't serve a single request."*  
> — Panel consensus

---

## APPENDIX: IMPROVEMENT PRIORITY MATRIX

| Priority | Task | Impact | Effort | Deadline |
|---|---|---|---|---|
| P0 | Get PostgreSQL running (SQLite fallback) | Unlocks all features | 30 min | Immediate |
| P0 | Remove upload `alert()` | Prevents demo embarrassment | 5 min | Immediate |
| P0 | Seed database with demo data | Makes demo realistic | 1 hour | Before demo |
| P1 | Connect dashboard to live API | Shows real metrics | 2 hours | Before demo |
| P1 | Connect compliance page to live API | Demos AI compliance | 2 hours | Before demo |
| P1 | Make login functional | Basic credibility | 30 min | Before demo |
| P1 | Add loading states to RFI chat | Polish | 30 min | Before demo |
| P2 | Implement basic schedule risk heuristic | Covers missing module | 3 hours | If time permits |
| P2 | Add few-shot examples to prompts | Improves AI quality | 1 hour | If time permits |
| P3 | Add citation rendering in chat | Builds trust | 2 hours | Post-hackathon |
