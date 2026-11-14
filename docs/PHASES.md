# Attestive — implementation plan

Each phase ends with working software: migrations, services, API, UI, tests and documentation.
A phase is not "done" because screens exist.

---

## Phase 1 — Foundation ✅

**Delivered**

* Repository structure, environment configuration, `.gitignore`, Docker Compose (PostgreSQL + API +
  web) and a backend Dockerfile.
* FastAPI application with domain layout, consistent error envelope, request logging and health
  endpoint.
* SQLAlchemy models and Alembic migration for identity, catalogue, learning state, assessment and
  engagement domains.
* JWT authentication: register, login, refresh rotation with replay detection, logout, current
  user. Argon2id hashing, hashed refresh tokens, origin checks, password change with session
  revocation.
* Progressive three-step onboarding persisted to profiles, preferences, subject interests and
  self-reported skill estimates.
* Subject/skill catalogue with seed data, pagination.
* Dashboard aggregated from real rows: level/XP, streak, study time, weekly goal, skills, path,
  7-day activity, assessments, achievements, recommendations.
* React + TypeScript + Vite + Tailwind + Framer Motion frontend: landing, features, about, login,
  registration, onboarding, dashboard, settings, 404.
* Design system primitives, protected routes, loading/error/empty states, responsive navigation.
* pytest suite covering auth, refresh rotation/replay, password change, catalogue, onboarding
  validation and dashboard aggregation.

**Verification**

```bash
cd backend && ./.venv/Scripts/python.exe -m pytest -q     # 16 tests
cd frontend && npm run build                              # typecheck + production build
```

---

## Phase 2 — Learning intelligence ✅

**Delivered**

1. **Diagnostic content**
   * Six curated diagnostics (one per subject, 36 questions) with MCQ, short answer and
     rubric-scored conceptual items, explanations and difficulty weights.
   * Per-subject curriculum: 6 courses, 37 ordered modules mapped to skills, each with a project.
   * Answer keys never leave the server before submission; review exposes them afterwards.

2. **Attempt lifecycle**
   * Start/resume (one in-progress attempt per assessment), autosave per question, submit with all
     answers required, immutable completed attempts.
   * Scoring service: exact/normalised MCQ, accepted-answer + keyword short answers, key-point
     rubric with partial credit for conceptual answers.
   * Ownership is enforced on every attempt endpoint; other students receive 404.
   * Coding items are typed and deliberately not auto-graded until the Phase 4 runner exists.

3. **Proficiency**
   * Per-skill evidence aggregated with difficulty weighting; self-report is a weak prior (85% on
     first evidence), later evidence moves estimates 45% at a time.
   * Confidence rises 25 points per assessment (capped at 100); source and timestamp recorded.
   * Attempts store score, proficiency estimate and weak-skill names as immutable evidence.

4. **Roadmap generation**
   * Planner targets modules for skills scored below 75%, adds breadth to reach three items, keeps
     curriculum order, adds a project last for students who prefer projects, archives the prior
     active plan.
   * Target level and duration derive from measured average and the student's weekly goal.
   * `RoadmapAgent` writes a validated, length-capped plan note via the model provider when available;
     otherwise a deterministic rationale is stored. `generated_by` records which happened.
   * Step completion is idempotent, awards XP once and never fabricates study minutes.

5. **UI**
   * Diagnostics index with status, score, resume/retake/review.
   * Question-by-question attempt flow with autosave, progress and answer validation.
   * Result page: score, proficiency, weak concepts, per-skill bars, answer review with explanations.
   * Roadmap page: subject switching, plan note with provenance, progress and step completion.
   * Dashboard empty states and recommendations link into the working flows.

**Deferred:** model-generated question variants and LLM-graded conceptual answers. The curated
banks make diagnostics reliable offline; generation will be added with the Phase 3 agent stack once
model output can be evaluated against the same rubrics. Coding-question grading belongs to Phase 4.

**Exit criteria met:** a new student can take a diagnostic, see measured proficiency per skill,
receive a persisted roadmap generated from the evidence, and resume it after signing out.

---

## Phase 3 — AI teaching ✅

**Goal:** a tutor that teaches rather than answers.

**Delivered**

* Provider abstraction (`ModelProvider`) with a hosted OpenAI-compatible adapter, model discovery (`/models`) and
  a `complete_text` path beside the schema-constrained `complete_json` used by the roadmap agent.
* `TeachingAgent` composing prose from measured proficiency, the active roadmap step, learning
  preferences, retrieved curriculum and the last ten messages. Modes: explain, hint (levels 1–4),
  worked example, check-my-understanding.
* `ai_conversations` / `conversation_messages` persistence with migration `9f2c1a7b4e10`; messages
  record the producing provider and the curriculum modules cited, sessions are per-student and
  resumable, and deletion is available.
* `/tutor/status`, conversation CRUD and message endpoints; ownership returns 404 to other students.
* Tutor UI: session list, transcript with per-message provenance, four teaching modes, follow-up
  suggestions, and a status banner naming the model or the exact setup problem.
* Offline behaviour: unavailable provider or model → `503 ai_unavailable`, nothing fabricated and
  nothing stored.
* A provider adapter for any hosted OpenAI-compatible chat-completions API (`AI_PROVIDER=openai`),
  selected by config alone. The adapter speaks the HTTP shape directly; no vendor SDK is required.

**Deferred:** LangGraph graphs, ChromaDB embeddings (retrieval is SQL over curated modules), token
streaming, model-generated practice questions and LLM-graded answers. Hints are tracked
conversationally; gating a solution reveal behind graded attempts arrives with the coding lab.

**Exit criteria met:** a signed-in student can start a subject-specific session, ask for an
explanation, hint or worked example, and return later to a persisted transcript — with the model
reported honestly when it is unavailable.

---

## Phase 4 — Practical learning

**Goal:** write, run and understand real code safely.

* `coding_exercises`, `test_cases`, `code_submissions` tables and services.
* Isolated runner service (separate container/process): per-run CPU/memory/time limits, ephemeral
  filesystem, no network, no secrets, output size caps, concurrency limits.
* Python, JavaScript, C++ toolchains; deterministic test harness output.
* `ExerciseAgent` generation with hidden tests; `EvaluationAgent` code review that explains failures
  and gives a next hint rather than the solution.
* Coding lab UI: editor, language selection, run/submit, test results, error explanations, AI review
  panel, hint ladder.
* Explicit refusal to run code if the sandbox is unavailable.

---

## Phase 5 — Engagement and analytics ✅

**Goal:** reward mastery and make progress legible.

**Delivered**

* XP award service wired to real events that exist today: diagnostic submission, completed roadmap
  steps and tutoring sessions. Idempotent per `(source_type, source_id)` with the ledger and cached
  total committed together.
* Streak evaluation with timezone-aware day boundaries, shared by the dashboard and analytics so the
  two cannot disagree.
* Achievement engine driven by seeded `criteria` JSON (streak days, skills at ≥60%, lessons,
  projects). Unlocks are recorded once and their XP reward is written in the same transaction. The
  coding-exercise criterion stays at zero until the Phase 4 runner is real.
* `GET /analytics/overview`: 30-day activity series, study time by kind, subject proficiency,
  assessment trend, weakest skills and deterministic revision suggestions.
* Insights page with study-time bars, time-by-kind, assessment trend, subject proficiency and a jump
  into the tutor for the weakest skills.

**Deferred:** weekly challenges, exportable progress summaries, model-written recommendations and
recommendation expiry scheduling.

**Exit criteria met:** a student can see where their time went, how proficiency moved after
assessments, and which skills to revisit — and milestones unlock exactly once.

---

## Phase 6 — Career development ✅

**Goal:** connect learning to a target role without promising employment.

**Delivered**

* Six curated, versioned role maps (`career_roles.version`) defining required skills as
  `(subject, skill, target, importance)`. Seeding validates every reference and refreshes role
  content, so a role can never point at a skill that does not exist.
* `career_service` gap analysis: per-skill `met` / `close` / `missing` (15-point band), weighted
  readiness score, strengths and priorities — computed only from measured `user_skills`.
* Deterministic career agent: recommendations ordered by importance then gap, and portfolio
  briefs annotated with the skills each one would demonstrate. `generated_by` records the
  provenance; no model call is required, so advice is stable and works offline.
* Mock interview flow: curated questions with rubrics, one resumable in-progress interview per
  role, per-answer scores storing awarded and missed rubric points, model answers released only
  after completion, readiness band and structured feedback. Completion awards XP once, records
  a zero-minute practice activity and unlocks `interview_ready`.
* Resume skill mapping: a claim is matched to a catalogue skill and marked verified only when
  non-self-reported evidence with ≥40% confidence exists; otherwise the evidence text says
  explicitly that it is unverified. Claims never change proficiency.
* Career UI: role cards with readiness, gap bars against targets, recommendations, portfolio
  briefs, the interview runner with rubric feedback, and the resume claim list.
* Non-guarantee copy on the role page, the interview panel and every completed interview.

**Deferred:** model-written CV feedback, salary data, live interviewer chat. The question bank is
curated, not generated, so rubric scoring stays explainable.

**Exit criteria met:** a student can pick a target role, see which measured skills fall short,
start a mock interview, answer every question, receive rubric-based feedback and a readiness
band, and see their resume claims labelled with the evidence behind them.

---

## Phase 7 — Production readiness ✅

* Rate limiting: per-process sliding window with a tighter auth budget, standard error envelope,
  `Retry-After`, health checks exempt; production validation refuses to start when disabled.
* Account lockout after configured failed passwords, with a cooling window cleared by success or
  password reset.
* Email verification and password reset: single-use SHA-256-hashed tokens, expiry, no account
  enumeration, session revocation on reset. Transports for Resend and SendGrid (HTTPS) and SMTP
  (stdlib, optional STARTTLS) are implemented, selected by `EMAIL_DELIVERY`; provider credentials
  are validated at startup. The console transport suppresses message bodies outside development so
  a reset link cannot leak into a production log.
* Security headers and a restrictive CSP on API responses, HSTS behind secure cookies, and CORS
  applied outside the rate limiter so browsers can read `429` bodies.
* Index review: `(user_id, status, completed_at)` on attempts and `(user_id, created_at)` on the XP
  ledger; `Cache-Control` on the public catalogue only, never on per-user responses.
* CI (`.github/workflows/ci.yml`): lint, compile, migrations + seed on an empty database, backend
  tests, frontend typecheck and production build.
* `scripts/load_test.py` reports ok/fail and p50/p95/p99 for read endpoints against a running API.
* `docs/RUNBOOK.md` (deploy, migrations and rollback, PostgreSQL backup/restore and drill,
  lockout operations, email delivery, rate-limit limitations, AI model versioning, load checks,
  incident triage) and `docs/SECURITY.md` (controls, assumptions, scanning commands, known gaps).

**Deferred:** a real mail transport, a shared rate-limit store for multi-instance deployments,
MFA, CSRF tokens, automated dependency/image scanning in CI and a staging environment.

**Exit criteria met:** unsafe production settings fail at startup, abusive traffic is throttled,
accounts lock and recover, verification and reset links work end to end, the suite and build run
in CI, and the operational procedures are written down.
