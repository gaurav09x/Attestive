# Attestive — Architecture

This document records the shape of the system and the decisions behind it. It is written to be
useful six months from now, not to restate the code.

---

## 1. System context

```text
Browser (React SPA)
   │  JSON over HTTPS, bearer access token + HttpOnly refresh cookie
   ▼
FastAPI application
   ├── API layer        routes → validation → service calls
   ├── Service layer    business rules, ownership checks, transactions
   ├── AI layer         (Phase 3+) provider abstraction → agents → LangGraph orchestration
   ├── Retrieval        (Phase 3+) ChromaDB embeddings for subject material
   └── Data layer       SQLAlchemy 2.0 async → PostgreSQL
                          │
                          └── Sandbox runner (Phase 4) for untrusted student code
```

PostgreSQL is the system of record. ChromaDB will hold embeddings for retrieval only; it is never
authoritative for users, progress, attempts or XP.

---

## 2. Key decisions

### ADR-001 — Async SQLAlchemy 2.0 with PostgreSQL, SQLite as a local fallback

The data layer uses `AsyncSession` and driver-agnostic types (`Uuid`, `JSON`, `String` enums) so the
same models run against `asyncpg` and `aiosqlite`. Unit tests use a throwaway SQLite file, which is
fast and isolated. Deployments use PostgreSQL via Docker Compose. Production config refuses a
SQLite URL, and SQLite is documented as a development convenience only.

*Consequence:* avoid PostgreSQL-only column types (JSONB, ARRAY) until a dialect-specific migration
is warranted. If retrieval or analytics later needs JSONB indexes, add them behind an Alembic
conditional migration rather than breaking local development.

### ADR-002 — Auth: short-lived access JWT + hashed, rotating refresh tokens

Access tokens (30 min) are stateless JWTs carried in the `Authorization` header. Refresh tokens
(14 days) are also JWTs, but their SHA-256 fingerprint is stored in `refresh_tokens` so they can be
rotated and revoked. Every refresh revokes the presented token and issues a new one. A replayed,
already-rotated token is treated as compromise and all of that user's sessions are revoked.

The refresh token is delivered in an `HttpOnly`, `SameSite=Lax` cookie scoped to `/api/v1/auth`;
the access token lives only in memory in the SPA. This keeps tokens out of `localStorage`, where a
single XSS would exfiltrate a long-lived credential.

Cookie-authenticated endpoints check the `Origin` header against configured origins. CORS alone is
not treated as CSRF protection.

*Known gap:* no rate limiting yet on login/refresh. Required before public exposure (Phase 7).

### ADR-003 — Domain-oriented backend layout

```text
api/      transport: routing, dependency wiring, status codes
schemas/  Pydantic contracts (request validation, response shaping)
services/ business rules, authorisation, transactions
models/   persistence
core/     config, security primitives, error envelope, logging
```

Routes do not contain business logic and services never return ORM objects to the transport layer
where a schema exists. This is what lets Phase 3 agents call services rather than routes, and lets
the same rule be enforced from a CLI or worker.

### ADR-004 — One error envelope, validation at the boundary

All failures return `{"error": {code, message, details?}}`, including framework validation errors
and unhandled exceptions. The frontend has a single parser (`ApiError`) and can map field errors.
Unhandled exceptions are logged with a request id and never leak stack traces to the client.

### ADR-005 — Data model shaped for evidence, not completion

Proficiency lives per skill (`user_skills`) with a `confidence` and `source`, so a self-reported
guess is distinguishable from an assessment result. Assessments record per-question responses so
weak concepts can be recomputed rather than overwritten by an aggregate score. XP is an append-only
ledger (`xp_transactions`) with a cached total on `users`.

`learning_activities` is the single source for study time and streaks; nothing derives "hours
learned" from page views.

### ADR-006 — AI is a set of services behind a provider abstraction (planned, Phase 3+)

```text
route/service → agent (Pydantic input/output) → model provider (hosted OpenAI-compatible | future)
                        │
                        └── LangGraph StateGraph for multi-step workflows
```

Rules that will govern the AI layer:

1. Agents return structured output validated by Pydantic; malformed output is retried, then falls
   back.
2. Agents never write to the database. They propose; a service validates and persists.
3. Every prompt includes only the student's relevant context (proficiency, goal, recent errors).
4. If the model provider is unavailable, endpoints return a deterministic fallback or a clear "AI unavailable"
   state — never fabricated content presented as generated teaching.

### ADR-007 — Untrusted code never runs in the API process (planned, Phase 4)

The coding lab will submit to a separate runner service with per-submission CPU/memory/time limits,
a read-only or ephemeral filesystem, no network, and no credentials. The API process will never
`exec` student code. Until that runner exists, the coding lab is not exposed as working.

### ADR-008 — Assessments are evidence; proficiency is an estimate with confidence

Diagnostics are curated content so the platform works without a model. Answer keys live only in
`questions.correct_answer` and are never serialised into an attempt payload. Scoring is
deterministic:

* MCQ: exact option index.
* Short answer: normalised accepted values, then keyword coverage with partial credit.
* Conceptual: key-point rubric with partial credit; correct at ≥60% coverage.
* Coding: deliberately unscored until the Phase 4 sandbox exists.

Each skill estimate stores `proficiency` **and** `confidence` **and** `source`. A self-reported seed
is explicitly weak (85% weight on the first assessment evidence); later evidence moves the estimate
45% at a time and confidence grows 25 points per assessment. Historical attempts keep their own
scores, so progress can be recomputed rather than overwritten.

### ADR-009 — Roadmap sequencing is deterministic; the model writes prose only

The roadmap planner selects from curated modules whose `skill_slugs` intersect measured weak skills,
adds breadth to a minimum of three items, preserves curriculum order, keeps a project last when the
student prefers projects, and archives the previous active plan. It never trusts model output to
choose or reference modules.

The roadmap agent (`app/ai/roadmap_agent.py`) receives that validated plan and may write a 2–3
sentence plan note through the model provider. Output is JSON-schema validated and length-capped; failure or an
unreachable provider falls back to a deterministic rationale. `learning_paths.generated_by` records
`deterministic` or `openai:<model>`, so the UI can state exactly what produced the note.

This keeps the learning sequence testable and reproducible while still using the model where it adds
value (explanation), not authority (state changes).

### ADR-010 — Design system as tokens + small primitives

Colours, radii and typography are CSS custom properties in Tailwind v4's `@theme`, consumed through
a handful of primitives (`Button`, `Panel`, `Field`, `Badge`, `Progress`, `EmptyState`, `Alert`).
Pages compose primitives instead of redefining surfaces. Framer Motion is used for state
transitions and page entry, not decoration, and animations respect `prefers-reduced-motion`.

---

## 3. Database schema

Implemented in `backend/migrations/versions/0001_initial_schema.py` (generated revision
`1cbd9fa10ad8`).

### Identity and preferences

| Table | Purpose | Notable constraints |
| --- | --- | --- |
| `users` | Identity, role, XP cache | unique lower-cased email (normalised in service), `is_active` |
| `refresh_tokens` | Revocable sessions | unique `token_hash`, index `(user_id, revoked_at)` |
| `user_profiles` | Education, experience, goal, weekly minutes, onboarding state | 1:1 with users |
| `learning_preferences` | Style, session length, theory/project bias | 1:1 with users |
| `user_subject_interests` | Chosen focus subjects | unique `(user_id, subject_id)` |
| `user_skills` | Per-skill proficiency estimate | unique `(user_id, skill_id)`, proficiency 0–100 |

### Catalogue

| Table | Purpose |
| --- | --- |
| `subjects` | Python, JavaScript, DSA, SQL, ML, system design |
| `skills` | Per-subject skills (`unique(subject_id, slug)`) |
| `courses` | Curated course metadata |
| `modules` | Ordered modules in a course (`unique(course_id, position)`), `skill_slugs` JSON for roadmap targeting, `is_project` flag |
| `lessons` | Ordered lessons in a module (`unique(module_id, position)`) |

### Learning state

| Table | Purpose |
| --- | --- |
| `learning_paths` | One active path per user/subject, with rationale and target level |
| `learning_path_items` | Ordered steps (course/project), completion state, immutable evidence on completed steps |
| `lesson_progress` | Per-user lesson status and minutes (`unique(user_id, lesson_id)`) |
| `learning_activities` | Append-only study events; drives streak and time |

### Assessment

| Table | Purpose |
| --- | --- |
| `assessments` | Diagnostic/quiz/practice sets per subject |
| `questions` | MCQ, short answer, conceptual, coding; JSON options + answer key |
| `assessment_attempts` | Attempt lifecycle, score, proficiency estimate, weak skills |
| `assessment_responses` | Per-question response, correctness, feedback |

### Engagement

| Table | Purpose |
| --- | --- |
| `xp_transactions` | Append-only XP ledger with reason and source |
| `achievements` | Definitions with machine-readable criteria JSON |
| `user_achievements` | Unlock records (`unique(user_id, achievement_id)`) |
| `learning_recommendations` | Next-activity suggestions with priority and dismissal |

Indexes exist on every foreign key used for per-user queries, plus composite indexes for
`learning_activities (user_id, occurred_on)` and `refresh_tokens (user_id, revoked_at)`.

### Not yet created

Tables for AI conversations/messages, coding exercises/submissions and projects will be added with
the phase that writes to them. Creating empty tables early adds migration surface without evidence
about their real query patterns.

---

## 4. Request lifecycle

1. CORS and request-id middleware run.
2. FastAPI resolves dependencies: DB session, bearer token → user (rejects inactive accounts).
3. Route validates the Pydantic body/query.
4. Service executes queries scoped by `user.id`, commits within a transaction.
5. Response is serialised through a Pydantic model; unknown fields never leak.

Session cleanup: the dependency closes the session per request; failed commits roll back and are
translated into the error envelope (e.g. duplicate email → 409).

---

## 5. Dashboard aggregation

A single service builds the payload from explicit queries (no N+1 relationship walking):

* study minutes and weekly goal from `learning_activities` summed by day;
* streak from distinct activity days, counted backwards from today (or yesterday, so an unbroken
  streak is not lost at midnight);
* lessons completed, skills ≥60%, active paths via `count()`;
* current path with `selectinload` of ordered items;
* upcoming assessments excluding subjects the student already completed an attempt for;
* achievements, top skills and recommendations via joins.

"Today" uses the profile timezone when valid, otherwise UTC.

---

## 6. Security posture (Phase 1)

Implemented: Argon2id hashing; enumeration-resistant login errors; hashed, rotated, revocable
refresh tokens; origin checks on cookie endpoints; role column for RBAC; per-user queries;
production config validation; secure-cookie enforcement; consistent error envelope that does not
leak internals; request logging with request ids; no secrets in the frontend bundle.

Outstanding before public deployment: rate limiting/backoff on auth, email verification, password
reset, CSP/security headers at the edge, dependency scanning in CI, and the sandbox runner for code.

---

## 7. Extension points

| Change | Where |
| --- | --- |
| Add an AI provider | new adapter beside the hosted-provider client; config switch only |
| Replace ChromaDB | retrieval interface consumed by agents |
| Add a subject | seed catalogue + content tables, no code change to the dashboard |
| Change the XP curve | `services/gamification.py` only |
| Add a protected route | service + schema + route, then register in `api/v1/router.py` |
