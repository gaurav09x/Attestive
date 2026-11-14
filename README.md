# Attestive

**An adaptive, AI-powered learning platform.** Attestive assesses what a student actually knows,
plans a route to their career goal, teaches at their level, and makes them prove mastery in code.

> Every student learns differently. Attestive adapts to the student, not the other way around.

---

## Current status

| Phase | Scope | Status |
| --- | --- | --- |
| **1 — Foundation** | Repository, FastAPI backend, PostgreSQL schema + migrations, JWT auth with rotating refresh tokens, progressive onboarding, subject/skill catalogue, real dashboard, design system, marketing site, tests | **Implemented** |
| **2 — Learning intelligence** | Diagnostic assessments with hidden answer keys, per-skill evidence updates, curated curriculum, persisted roadmaps with optional model-written plan notes, assessment/roadmap UI | **Implemented** |
| **3 — AI teaching** | Hosted-model teaching agent, persisted tutor conversations with memory, curriculum-grounded context, progressive hints, tutor chat UI | **Implemented** (retrieval is SQL over the curated curriculum; LangGraph, ChromaDB embeddings and token streaming are deferred) |
| 4 — Practical learning | Coding lab, sandboxed execution, AI code review, exercise evaluation | Not started |
| **5 — Engagement** | XP ledger wired to assessments, roadmap steps and tutoring, data-driven achievement unlocks, streaks, analytics API, Insights UI | **Implemented** (weekly challenges deferred) |
| **6 — Career development** | Versioned role skill maps, gap analysis and readiness, deterministic study and portfolio recommendations, rubric-scored mock interviews, resume claims with evidence labels | **Implemented** |
| **7 — Production readiness** | Rate limiting, account lockout, email verification and password reset, security headers/CSP, index review, CI, load-check script, runbook and security docs | **Implemented** (no mail provider; rate limits are per process) |

Phases 1 and 2 are real: accounts, sessions, onboarding, catalogue, diagnostics, proficiency,
roadmaps and the dashboard all read and write the database. Anything not built yet is labelled in
the UI rather than simulated. A brand-new account shows zeros, because that student has not studied
yet. Coding questions are stored as a supported type but are not auto-graded until the sandboxed
Coding Lab in Phase 4.

Detailed plan: [`docs/PHASES.md`](docs/PHASES.md). Architecture decisions:
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Deployment:
[`docs/DEPLOY.md`](docs/DEPLOY.md) (Render blueprint, AWS outline, hosted model setup).

---

## Quick start (no Docker required)

Requirements: Python 3.11+, Node 20+.

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows (Git Bash / PowerShell):
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
# macOS / Linux:
# source .venv/bin/activate && pip install -r requirements-dev.txt

cp .env.example .env          # optional: edit SECRET_KEY
./.venv/Scripts/python.exe -m app.cli init    # migrations + catalogue seed
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

* API: <http://localhost:8000>
* Interactive docs: <http://localhost:8000/docs>
* Health: <http://localhost:8000/api/v1/health>

Without Docker the app uses an async SQLite file at `backend/data/attestive.db`. This is a
**development fallback only**; PostgreSQL is required in production and the app refuses to start in
`ENVIRONMENT=production` with SQLite.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env        # VITE_API_URL=http://localhost:8000/api/v1
npm run dev
```

Open <http://localhost:5173>, create an account, complete the three onboarding steps, and the
dashboard will show your real (initially empty) state.

### 3. Tests

```bash
cd backend
./.venv/Scripts/python.exe -m pytest -q     # 41 tests
```

---

## Docker Compose (PostgreSQL + API + web)

```bash
cp backend/.env.example backend/.env      # optional overrides
docker compose up --build
```

* PostgreSQL 16 on `localhost:5432`
* API on `localhost:8000` (runs migrations and seeds the catalogue on start)
* Vite dev server on `localhost:5173`

Set `SECRET_KEY` in the environment or a root `.env` before any shared deployment. The tutor
calls any hosted OpenAI-compatible API (`AI_PROVIDER=openai`, `OPENAI_*`); set
`AI_PROVIDER=disabled` for deterministic-only runs.

---

## What Phase 1 actually does

### Authentication

* Register / login / logout / refresh / current-user endpoints.
* Argon2id password hashing (`pwdlib`), 30-minute JWT access tokens.
* Refresh tokens are 14-day JWTs stored **hashed** (SHA-256) in `refresh_tokens`, rotated on every
  use. Replaying a rotated token revokes every session for that user.
* Refresh token travels in an `HttpOnly`, `SameSite=Lax`, path-scoped cookie; the access token is
  held in memory by the frontend and never persisted to `localStorage`.
* Cookie endpoints reject foreign `Origin` headers, not just foreign CORS requests.
* Changing a password revokes all refresh tokens.

### Onboarding and profile

Three progressive steps collect education, experience, career direction, target role, subjects of
interest, learning style, session length, weekly study goal and project/theory preference. Choices
are persisted in `user_profiles`, `learning_preferences`, `user_subject_interests` and
`user_skills` (a clearly labelled *self-reported* estimate with 10% confidence).

### Diagnostic assessments (Phase 2)

* One curated six-question diagnostic per subject, mixing multiple choice, short answer and
  rubric-scored conceptual questions. Answer keys and explanations never leave the server before
  submission.
* Attempts autosave per question and are resumable. Submission requires every question to be
  answered, scores each item, and is rejected once the attempt is completed.
* Conceptual answers are graded against key points (partial credit); short answers against accepted
  values and keywords. Coding items are typed but not graded until Phase 4 — the UI says so.
* Attempts are immutable evidence and visible only to their owner.

### Proficiency (Phase 2)

Per-skill estimates are updated by the assessment service. A self-reported onboarding seed is a
weak prior (85% weight on the first real evidence); later evidence moves estimates less and
confidence rises. Attempt scores, weak-skill names, proficiency and confidence are persisted.

### Roadmaps (Phase 2)

After submission, the planner selects modules from curated curriculum whose skills were weak, adds
breadth to reach at least three items, places a project last when the student prefers projects, and
archives the previous active plan for that subject. The sequence is deterministic and validated; if
a model provider is configured, the roadmap agent writes the plan note (validated, length-capped, model named
in `generated_by`). Without a model the note is written deterministically.

Step completion is idempotent and awards XP once. It deliberately does **not** invent study minutes.

### AI tutor (Phase 3)

* Per-student conversations in `ai_conversations` / `conversation_messages`, resumable after signing
  out. Every assistant message records the `provider` (`openai:<model>`) that produced it and the
  curriculum modules it was grounded in, so model output is never anonymous.
* Each reply is built from the student's measured proficiency (weak and strong skills), their active
  roadmap step for that subject, learning preferences and the last ten messages of the conversation.
* Retrieval scores question terms against curated module and course text in the database and puts
  the best matches in the prompt. The catalogue is small, so this keeps teaching grounded without a
  second service; ChromaDB embeddings remain the plan for a larger corpus.
* Hint mode escalates one level at a time (1–4) from prior hints in the same session and is instructed
  not to reveal the solution. Explain, worked-example and check-my-understanding modes share the
  same persisted transcript.
* Level starts from measured proficiency when left on `auto` and is stored on the conversation.
* When the model provider is disabled, unreachable or missing the configured model, `/tutor/status` says exactly
  why and message sends return `503 ai_unavailable`. No assistant message is stored, so a failed
  reply can never look like teaching.

### Engagement and analytics (Phase 5)

* XP is an append-only ledger with a cached total. Assessments, completed roadmap steps and the first
  message of a tutoring session award XP through one idempotent service, so replaying a completion
  cannot pay twice.
* Achievements are **data**: `achievements.criteria` holds a type and threshold (streak days, skills
  at ≥60%, completed projects, lessons). Evaluation runs after the events that can satisfy them and
  unlocks each row once, awarding its XP reward in the same transaction. Coding-exercise criteria
  stay at zero until the Phase 4 runner exists rather than counting something that never ran.
* Tutoring records a study event with **zero measured minutes**: the day counts toward a streak, but
  study time is never inflated from a chat.
* `GET /analytics/overview` aggregates a 30-day activity series, study time by activity kind,
  proficiency per subject, the last ten completed attempts, weakest measured skills and deterministic
  revision suggestions — all from the student's rows, with empty states for new accounts.
* Insights page: 30-day study chart, time-by-kind, assessment trend, subject proficiency bars and the
  weakest skills with a direct link into the tutor.

### Career development (Phase 6)

* Six curated, versioned role maps define required skills as `(subject, skill, target,
  importance)`. Seeding validates every reference, so a role cannot point at a skill that does
  not exist.
* Gap analysis compares each requirement with measured proficiency: `met`, `close` (within 15
  points) or `missing`, plus a weighted readiness score. Readiness never rises from a resume
  claim.
* Recommendations and portfolio briefs are deterministic (`generated_by: deterministic`): highest
  importance and largest gap first, each brief labelled with the skills it would demonstrate.
* Mock interviews use curated questions with rubrics. One resumable in-progress interview per
  role, per-question scores with the awarded and missed rubric points, model answers only after
  completion, and a readiness band with structured feedback. Completion awards XP once and
  unlocks `interview_ready`.
* Resume claims are matched to catalogue skills and marked verified only when non-self-reported
  evidence with ≥40% confidence exists; otherwise they are explicitly unverified.
* Every role and interview response carries a non-guarantee disclaimer: preparation, not a
  promise of employment.

### Production readiness (Phase 7)

* Sliding-window rate limiting per process (tighter for `/auth/*`) returning the standard error
  envelope with `Retry-After`; health checks are exempt.
* Account lockout after five failed passwords for 15 minutes, cleared on success or reset.
* Email verification (48 h) and password reset (60 min) with single-use hashed tokens, no account
  enumeration, and full session revocation on reset. Delivery is `console` (logged) or
  `disabled` — no mail provider is configured yet.
* Security headers and a restrictive CSP on API responses; HSTS when secure cookies are enabled.
* Production startup validation now also requires HTTPS `APP_BASE_URL` and enabled rate limiting.
* CI runs lint, compile, migrations-and-seed on an empty database, the backend suite, and the
  frontend typecheck and build. `scripts/load_test.py` reports latency percentiles.
* `docs/RUNBOOK.md` covers deployment, migrations and rollback, PostgreSQL backup/restore and a
  restore drill, lockout operations, email delivery, rate-limit limits, AI model versioning and
  incident triage. `docs/SECURITY.md` records controls, assumptions, scanning commands and known
  gaps.

### Dashboard

Computed per request from the student's rows: XP and level, study minutes, streak, weekly goal,
lessons completed, skills at ≥60% proficiency, current learning path, seven-day activity series,
top skills, upcoming assessments, achievements and recommendations. Each section has an honest
empty state, and the roadmap/diagnostic empty states link to the working flows.

---

## Repository layout

```text
Attestive/
├── backend/
│   ├── app/
│   │   ├── api/deps.py                 # auth dependency, trusted-origin check
│   │   ├── ai/                         # provider, retrieval, teaching + roadmap agents
│   │   ├── api/v1/routes/              # auth, users, catalog, dashboard, tutor, health
│   │   ├── core/                       # settings, security, errors, logging
│   │   ├── db/                         # base, session, seed
│   │   ├── models/                     # SQLAlchemy domain models
│   │   ├── schemas/                    # Pydantic request/response contracts
│   │   ├── services/                   # business logic (auth, profile, dashboard, gamification)
│   │   ├── cli.py                      # migrations + seed entrypoint
│   │   └── main.py
│   ├── migrations/                     # Alembic (async env)
│   ├── tests/                          # pytest + httpx ASGI tests
│   ├── Dockerfile
│   └── requirements*.txt
├── frontend/
│   ├── src/
│   │   ├── components/                 # design system, layouts, charts
│   │   ├── lib/                        # API client, auth context, types, formatting
│   │   ├── pages/                      # marketing + authenticated pages
│   │   ├── routes/guards.tsx
│   │   └── App.tsx
│   └── vite.config.ts
├── docs/ARCHITECTURE.md
├── docs/PHASES.md
└── docker-compose.yml
```

---

## API surface (Phase 1)

All paths are prefixed with `/api/v1`.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | — | Liveness, DB reachability, AI provider |
| POST | `/auth/register` | — | Create account, issue tokens, set refresh cookie |
| POST | `/auth/login` | — | Authenticate, rotate session |
| POST | `/auth/refresh` | cookie | Rotate refresh token, issue access token |
| POST | `/auth/logout` | cookie | Revoke refresh token, clear cookie |
| GET | `/auth/me` | bearer | Current user + interests + skills |
| GET | `/users/me` | bearer | Full profile payload |
| PATCH | `/users/me` | bearer | Update name, headline, bio, role, goal, timezone |
| POST | `/users/me/onboarding` | bearer | Persist onboarding and seed skill estimates |
| POST | `/users/me/password` | bearer | Change password, revoke other sessions |
| GET | `/catalog/subjects` | — | Paginated subject catalogue |
| GET | `/catalog/subjects/{slug}/skills` | — | Skills for a subject |
| GET | `/dashboard` | bearer | Aggregated student dashboard |
| GET | `/assessments` | bearer | Diagnostics per subject with attempt status |
| POST | `/assessments/{id}/attempts` | bearer | Start or resume an attempt |
| GET | `/assessments/attempts/{id}` | bearer | Attempt with saved answers (no keys) |
| PUT | `/assessments/attempts/{id}/responses/{question_id}` | bearer | Autosave one answer |
| POST | `/assessments/attempts/{id}/submit` | bearer | Score, update proficiency, create roadmap |
| GET | `/assessments/attempts/{id}/review` | bearer | Answers, explanations, per-skill results |
| GET | `/roadmaps` | bearer | All roadmaps for the student |
| GET | `/roadmaps/{id}` | bearer | One roadmap |
| PATCH | `/roadmaps/{id}/items/{item_id}` | bearer | Start/complete a roadmap step |
| GET | `/tutor/status` | bearer | Tutor availability, provider and model |
| GET | `/tutor/conversations` | bearer | Tutor sessions for the student |
| POST | `/tutor/conversations` | bearer | Start a tutoring session |
| GET | `/tutor/conversations/{id}` | bearer | Session with full message history |
| DELETE | `/tutor/conversations/{id}` | bearer | Delete a session |
| POST | `/tutor/conversations/{id}/messages` | bearer | Send a message, receive a tutoring reply |
| GET | `/analytics/overview` | bearer | 30-day activity, proficiency, trends and weak skills |
| POST | `/auth/verify-email` | — | Consume a single-use verification token |
| POST | `/auth/verify-email/resend` | bearer | Create a fresh verification link |
| POST | `/auth/password-reset/request` | — | Request a reset link (no account enumeration) |
| POST | `/auth/password-reset/confirm` | — | Set a new password, revoke sessions |
| GET | `/career/roles` | bearer | Role summaries with readiness per role |
| GET | `/career/roles/{slug}` | bearer | Gap analysis, recommendations, portfolio briefs |
| GET | `/career/interviews` | bearer | Recent mock interviews |
| POST | `/career/interviews` | bearer | Start or resume an interview for a role |
| GET | `/career/interviews/{id}` | bearer | Interview with questions and scores |
| POST | `/career/interviews/{id}/responses` | bearer | Score one answer against its rubric |
| POST | `/career/interviews/{id}/complete` | bearer | Finish, score, award XP and achievements |
| GET | `/career/resume-skills` | bearer | Claims with verified/unverified evidence |
| POST | `/career/resume-skills` | bearer | Map a resume claim to a catalogue skill |
| DELETE | `/career/resume-skills/{id}` | bearer | Remove a claim |

Errors share one envelope:

```json
{ "error": { "code": "validation_error", "message": "Some fields are invalid.", "details": [{ "field": "password", "message": "..." }] } }
```

---

## Configuration

Backend settings come from environment variables or `backend/.env` (see `backend/.env.example`).
Never commit `.env`.

| Variable | Default | Notes |
| --- | --- | --- |
| `SECRET_KEY` | insecure dev value | Must be ≥32 random chars in production |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/attestive.db` | `postgresql+asyncpg://…` for Postgres |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS + origin validation |
| `COOKIE_SECURE` | `false` | Must be `true` in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` | Refresh token lifetime |
| `AI_PROVIDER` | `openai` | any OpenAI-compatible host, or `disabled` for deterministic-only |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Base URL of the hosted provider (Z.ai, OpenAI, Groq, vLLM, …) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model id the provider serves |
| `OPENAI_API_KEY` | — | Server-side key; never a `VITE_` variable |
| `OPENAI_TIMEOUT_SECONDS` | `60` | Cap on a hosted tutor reply |
| `AI_ROADMAP_ENABLED` | `true` | When false, roadmap notes are deterministic |
| `ROADMAP_AI_TIMEOUT_SECONDS` | `12` | Hard cap on the plan-note call |
| `APP_BASE_URL` | `http://localhost:5173` | Base for verification and reset links; HTTPS required in production |
| `MAX_FAILED_LOGINS` | `5` | Failed passwords before an account locks |
| `LOCKOUT_MINUTES` | `15` | Lockout cooling window |
| `EMAIL_DELIVERY` | `console` | `console` (dev), `disabled`, `resend`, `sendgrid` or `smtp` |
| `EMAIL_FROM` | `Attestive <no-reply@localhost>` | Verified sender at the provider |
| `EMAIL_API_KEY` | — | Required for `resend` / `sendgrid` |
| `SMTP_HOST` / `SMTP_PORT` | — / `587` | Required for `smtp` |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | — | SMTP credentials (STARTTLS by default) |
| `VERIFY_TOKEN_TTL_HOURS` | `48` | Verification link lifetime |
| `RESET_TOKEN_TTL_MINUTES` | `60` | Reset link lifetime |
| `RATE_LIMIT_ENABLED` | `true` | Required in production |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `20` | Per-process budget for `/auth/*` |
| `RATE_LIMIT_DEFAULT_PER_MINUTE` | `120` | Per-process budget for other endpoints |

`ENVIRONMENT=production` validates the security-critical settings and fails fast if they are unsafe.

---

## Deliberately not implemented yet

* Coding lab and sandboxed execution (Phase 4, blocked by ADR-007 until a separate runner
  exists). UI surfaces are labelled by phase instead of pretending to work.
* Weekly challenges and recommendation generation by a model. Recommendations currently come from
  assessment evidence rather than a scheduled agent.
* Tutor token streaming, LangGraph orchestration, ChromaDB embeddings and LLM-graded answers. The
  tutor currently answers in one piece from a SQL-grounded context.
* Automatic grading of coding questions (Phase 4). The assessment schema supports them; the
  diagnostic banks currently use MCQ, short answer and conceptual items.
* A configured mail provider. Resend, SendGrid and SMTP transports are implemented and validated
  at startup, but delivery needs the operator's sender domain and credential
  (`EMAIL_DELIVERY`, `EMAIL_FROM`, `EMAIL_API_KEY` or `SMTP_*`).
* A shared rate-limit store and MFA/CSRF hardening. Rate limits are per process, so a
  multi-instance deployment needs Redis; access tokens remain valid until expiry after a password
  change.
* Automated dependency and image scanning in CI. The commands are documented in
  `docs/SECURITY.md` and run manually.
* Docker is not installed on the machine this was developed on, so the Compose stack could not be
  executed here; it is provided for a Docker-capable host.
* The model-written roadmap-note path is implemented; when the provider returns malformed JSON or
  times out, the deterministic fallback is stored. Check `learning_paths.generated_by` changes from
  `deterministic` to `openai:<model>`. Roadmap sequencing does not depend on the model at all.
