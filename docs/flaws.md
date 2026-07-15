# EPC-Intel judge stress-test report

**Assessment date:** 2026-07-15  
**Scope:** local running application at `localhost:8000`, frontend production build/lint, and focused source review.  
**Verdict:** a compelling prototype with a polished shell. The highest-risk authorization, project-scope, document-type, and non-deterministic-score issues were remediated on 2026-07-15; the remaining items below still require production work.

## Remediation status (2026-07-15)

| Finding | Status |
| --- | --- |
| Public project-data endpoints | **Fixed:** protected endpoints now require bearer authentication. |
| Project isolation | **Fixed for the current model:** explicit `project_members` access checks scope Documents, RFI, Compliance, and Dashboard APIs. |
| CSV accepted by PDF document ingestion | **Fixed:** Documents accepts PDFs only; CSV import remains in Schedule Risk. |
| Non-deterministic risk scores | **Fixed:** weather/vendor placeholder inputs are deterministic zero until real versioned data is integrated. |
| CSV WBS dependency references | **Fixed:** importer resolves in-file WBS references to task IDs and rejects unknown dependencies. |
| RFI session persistence and cross-project retrieval | **Fixed:** chat sessions are created/validated per user/project and retrieval is project-scoped. |
| Database compatibility failure | **Mitigated:** existing SQLite databases are upgraded for `page_count`; replace this compatibility path with a formal Alembic upgrade before production. |

## Reusable judge prompt

> You are a skeptical senior judge for an EPC/data-centre AI product. Treat every claim as unproven until the live workflow, API behaviour, and source code demonstrate it. Test happy paths and adverse paths: unauthenticated access, role boundaries, invalid and oversized uploads, malformed CSVs, missing downstream services, repeated calculations, stale data, concurrent actions, and AI-provider failure. For every issue, report: (1) severity, (2) reproducible evidence, (3) user/business impact, and (4) the smallest credible remediation. Do not award points for UI-only functionality, mocked results presented as predictions, or error handling that hides failed persistence. Finish with a go/no-go recommendation.

## Tests run

| Check | Result |
| --- | --- |
| Frontend production build | Pass (`next build`) |
| Frontend lint | **Fail:** 18 errors, 5 warnings |
| `GET /health` | Pass: 200 |
| `GET /api/v1/documents` without a bearer token | **200** |
| `GET /api/v1/rfi` without a bearer token | **200** |
| `GET /api/v1/compliance/deviations` without a bearer token | **200** |
| `GET /api/v1/dashboard/summary` without a bearer token | **200** |
| `GET /api/v1/projects` without a bearer token | Expected protection observed: 401 |
| RFI question: generator clearance | API returned 200, but Gemini returned quota exhaustion; local retrieval fallback returned the stored 900 mm excerpt |
| Existing SQLite database with an older `documents` schema | Previously failed document listing with `no such column: documents.page_count`; fixed locally with a startup compatibility patch |

## Confirmed flaws

### P0 — unauthenticated users can read project data

**Evidence:** The four unauthenticated `GET` requests above returned 200. `documents`, RFI listing, compliance deviations, and dashboard summary have no `get_current_user` dependency.

**Impact:** Any party able to reach the API can retrieve project documents, RFIs, deviations, schedule risk, and dashboard data. This is unacceptable for client, vendor, and project information.

**Fix:** Require authentication on every project-data route; apply project scoping from a trusted selected-project claim/session rather than an arbitrary request header. Add automated 401/403 tests for every route.

### P0 — project isolation is not enforced

**Evidence:** `get_project_db` explicitly yields a normal session and does not apply its `project_id` header. Several list/search endpoints either accept an optional caller-controlled header or query all records. RFI retrieval explicitly uses `project_id=None`.

**Impact:** Even after login, a user can request another project's data by changing a header, and RFI answers may include content from another project.

**Fix:** Derive authorized project membership server-side, filter every query by that project, and add database-level row-level security for production.

### P0 — schedule CSV is advertised in the Documents page but cannot be ingested there

**Evidence:** The Documents form accepts CSV and offers `Schedule (CSV)`, but its upload endpoint sends all files to `parse_pdf_bytes()` during document ingestion. A CSV uploaded there is stored and then fails PDF parsing. The dedicated schedule importer is a different endpoint.

**Impact:** Users follow the visible UI and get a failed "document" rather than schedule tasks/risk analysis. This was observed during the upload workflow.

**Fix:** Remove CSV from the Documents upload accept list/type picker, or route `doc_type=schedule` directly to `/schedule/import`; validate MIME type and show an actionable status.

### P0 — risk scores are non-deterministic and therefore not auditable

**Evidence:** `compute_weather_severity()` and `compute_vendor_otd_history()` call `random.uniform()` for every score calculation. The calculated score is stored anew each time `/schedule/risk` is requested.

**Impact:** The same schedule can receive different scores and contributing factors on refresh. This cannot support project decisions, auditability, or a credible "predictive" claim.

**Fix:** Replace random stubs with versioned, sourced inputs or clearly label the function a simulation. Store input snapshots, model version, timestamp, and a single immutable result per run.

### P1 — CSV dependencies do not resolve to imported task IDs

**Evidence:** The CSV importer stores `dependencies` unchanged. The provided template uses WBS values such as `"1.1"`, while the critical-path engine expects database task UUIDs. Consequently graph edges do not connect to imported predecessor tasks.

**Impact:** Critical-path and upstream-slippage calculations are wrong for normal human-authored CSVs.

**Fix:** Import in two passes: map WBS codes to newly created task IDs, validate unknown/cyclic dependencies, then store canonical UUID dependencies. Report rejected rows and reasons.

### P1 — AI chat is dependent on an unavailable provider and its fallback is not an answer engine

**Evidence:** The live Gemini request returned `429 RESOURCE_EXHAUSTED`. The current fallback lists the top two retrieved chunks; it does not synthesize or validate an answer.

**Impact:** Chat quality drops from an assistant to raw excerpts whenever quota/network fails. Provider error details were previously exposed to the user.

**Fix:** Monitor quota before release, use a resilient provider/model strategy with timeout/retry/backoff, and clearly label retrieval-only mode. Add evaluation cases with expected answers and citations.

### P1 — chat conversation persistence silently fails

**Evidence:** The frontend sends a hard-coded `demo-session-123`, but `ChatMessage.session_id` has a foreign key to `chat_sessions`. No session is created for that ID. Persistence exceptions are caught and hidden; the transaction is rolled back only after the failure.

**Impact:** The interface appears to work, but chat history/audit trail is not reliably saved. This is dangerous for RFIs, which need traceability.

**Fix:** Create a real session after authentication, pass its ID from the server, scope it to project/user, and return persistence failures explicitly. Add an integration test verifying messages appear in the session history.

### P1 — upload controls lack essential safety limits

**Evidence:** The Document upload endpoint has no extension/MIME allow-list enforcement, no maximum file size, no malware scanning, and reads the entire upload into memory (`await file.read()`).

**Impact:** A large or malicious upload can exhaust memory/disk, create unusable records, or reach parsers/storage unexpectedly.

**Fix:** Enforce server-side type and size limits, stream uploads, scan files, reject unsupported content before storage, and delete/mark failed objects consistently.

### P1 — schema evolution is fragile

**Evidence:** A pre-existing SQLite database was missing `documents.page_count`; `Base.metadata.create_all()` creates tables but does not alter them, causing the Documents screen to fail with HTTP 500. A local SQLite startup patch now works around this specific missing column.

**Impact:** Future model changes can again break a deployed database at runtime. The workaround does not replace versioned migrations.

**Fix:** Use Alembic migrations as the only schema upgrade path, run them during deployment, and test upgrades from the previous release database.

### P2 — frontend quality gate is currently red

**Evidence:** `npm run lint` reported 18 errors and 5 warnings. Errors include multiple `any` types and React synchronous `setState`-in-effect violations in auth/modal code; warnings include unused imports/state.

**Impact:** CI cannot enforce the stated frontend quality bar; unsafe typing obscures API contract regressions.

**Fix:** Resolve all lint errors, add typed API response models, and make lint/build/test required CI checks.

### P2 — misleading or incomplete UX states

**Evidence:** Document loading failures are only written to the browser console; the initial page has no user-visible load/error/empty-state distinction. The RFI page uses a shared static session ID. Schedule import automatically selects the first accessible project rather than requiring an explicit project choice.

**Impact:** Users can misinterpret stale, missing, or cross-project data as valid outcomes.

**Fix:** Add explicit loading/error/retry states, project context in the header, and user-selected project scoping.

### P2 — development secrets and defaults are unsafe for deployment

**Evidence:** Configuration includes default JWT secrets and MinIO credentials; login cookies use `secure=False`. The repository contains demo accounts/passwords in the seed script.

**Impact:** A deployment that inherits defaults can expose accounts or enable token forgery.

**Fix:** Fail startup when production secrets are absent/default, use managed secrets, set secure cookie attributes under HTTPS, and keep demo credentials strictly outside production seed paths.

## Go/no-go recommendation

**No-go for production or client data.** Address the P0 authorization/isolation defects and deterministic schedule-risk issue before any external demonstration involving real project information. For a controlled hackathon demo, clearly label it as demo data, disable unauthenticated endpoints, remove the CSV-from-Documents path, and disclose that AI answers may enter retrieval-only mode when the provider quota is unavailable.
