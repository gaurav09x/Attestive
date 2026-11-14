# Deploying Attestive

The application is a **Python/FastAPI API + PostgreSQL + static React build**. It
is not a Workers/edge app, so Cloudflare-Workers hosting (including Freebuff
Sites) cannot run it. Deploy the API to a container host and the frontend to a
static host.

Two paths are documented: Render (fastest, blueprint included) and AWS.

---

## 0. What has to be true before it is public

| Setting | Requirement |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | ≥32 random chars, unique |
| `DATABASE_URL` | `postgresql+asyncpg://…` (set by the platform) |
| `COOKIE_SECURE` | `true` |
| `FRONTEND_ORIGIN` | exact static-site origin, `https://…`, no trailing slash |
| `APP_BASE_URL` | same origin; used in verification and reset links |
| `EMAIL_DELIVERY` | `disabled` (boots, sends nothing) or `resend`, `sendgrid`, `smtp` + credentials |
| `AI_PROVIDER` | `openai` with a hosted model (`disabled` for deterministic-only) |
| `COOKIE_SAMESITE` | `none` when the frontend and API are different origins, `lax` when same-origin |

Startup fails fast when a requirement is violated. Rate limiting must stay on.

---

## 1. Render (fast path)

`render.yaml` in the repository root defines:

* `attestive-db` — managed PostgreSQL (free plan)
* `attestive-api` — Docker service from `backend/Dockerfile`, runs migrations and
  seeds on start, health check `/api/v1/health`
* `attestive-web` — static site, `npm ci && npm run build`, SPA rewrite to
  `index.html`

Steps:

1. Put the code in a GitHub repository (the working copy has no commits yet):

   ```bash
   git add -A
   git commit -m "Attestive: production-ready application"
   git branch -M main
   git remote add origin https://github.com/<you>/attestive.git
   git push -u origin main
   ```

   `backend/.env` is gitignored, so the model key is never pushed.
2. Render → **New → Blueprint**, select the repository, apply.
3. Fill the variables marked `sync: false`:

   | Variable | Value |
   | --- | --- |
   | `FRONTEND_ORIGIN` | `https://attestive-web.onrender.com` (your static site URL) |
   | `APP_BASE_URL` | same as `FRONTEND_ORIGIN` |
   | `OPENAI_BASE_URL` | provider base URL, e.g. `https://api.groq.com/openai/v1` |
   | `OPENAI_MODEL` | a model your provider serves, e.g. `openai/gpt-oss-120b` |
   | `OPENAI_API_KEY` | provider key (secret) |
   | `EMAIL_FROM` | verified sender, e.g. `Attestive <no-reply@mail.example.com>` |
   | `EMAIL_API_KEY` | mail provider key (secret) |

   The blueprint ships with `EMAIL_DELIVERY=disabled` so the API boots without a
   mail provider. To send verification and reset email, change `EMAIL_DELIVERY`
   to `resend`, `sendgrid` or `smtp` **and** set `EMAIL_FROM` plus
   `EMAIL_API_KEY` (or `SMTP_HOST`/`SMTP_USERNAME`/`SMTP_PASSWORD`) in the same
   change: a provider selected without credentials is a hard startup error.
   Leaving `OPENAI_API_KEY` empty is safe — the API boots and `/tutor/status`
   reports the tutor as unavailable.

4. On the static site, set `VITE_API_URL` to
   `https://attestive-api.onrender.com/api/v1`, then trigger a rebuild — Vite
   inlines it at build time.
5. Redeploy the API after the variables are set. Migrations and seeding run in the
   start command; the first deploy creates the schema.

Notes:

* Free web services sleep after inactivity. The first request can take ~30 s.
* Free PostgreSQL on Render is time-limited; check the current offer before
  relying on it. Move to a paid plan or another provider for anything durable.
* The startup command runs `python -m app.cli init` on every boot. It is
  idempotent (upgrade to head + seed), but concurrent instances should be scaled
  to one during a deploy.

---

## 2. AWS outline

**Database** — RDS PostgreSQL (db.t4g.micro), private subnet, security group
allowing only the API. Connection string:
`postgresql+asyncpg://user:pass@host:5432/attestive`.

**API** — build and push the image, then run it on ECS Fargate behind an ALB
(simplest managed path) or on a single EC2 instance with Docker:

```bash
docker build -t attestive-api ./backend
docker run -d --name attestive-api -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL='postgresql+asyncpg://…' \
  -e SECRET_KEY='…' -e COOKIE_SECURE=true \
  -e FRONTEND_ORIGIN='https://app.example.com' \
  -e APP_BASE_URL='https://app.example.com' \
  -e AI_PROVIDER=openai -e OPENAI_BASE_URL='…' \
  -e OPENAI_MODEL='…' -e OPENAI_API_KEY='…' \
  -e EMAIL_DELIVERY=resend -e EMAIL_FROM='…' -e EMAIL_API_KEY='…' \
  attestive-api
```

Run migrations once per release before the new task starts:
`docker run --rm … attestive-api python -m app.cli init`.

**Frontend** — `npm ci && npm run build` with `VITE_API_URL` pointing at the API,
then upload `dist/` to S3 behind CloudFront. Enable HTTPS, set the SPA fallback
(403/404 → `/index.html`), and put the same origin into `FRONTEND_ORIGIN` and
`APP_BASE_URL`.

**TLS** — terminate at the ALB/CloudFront. The app sets HSTS when
`COOKIE_SECURE=true`.

---

## 3. The AI tutor in production

The tutor calls a hosted OpenAI-compatible endpoint:

```env
AI_PROVIDER=openai
OPENAI_BASE_URL=https://api.groq.com/openai/v1  # or any OpenAI-compatible base
OPENAI_MODEL=openai/gpt-oss-120b
OPENAI_API_KEY=…                                # server-side only, never VITE_*
OPENAI_TIMEOUT_SECONDS=60
AI_ROADMAP_ENABLED=true
ROADMAP_AI_TIMEOUT_SECONDS=12
```

The provider is called with `POST {OPENAI_BASE_URL}/chat/completions` and
`Authorization: Bearer …`; model discovery uses `GET {OPENAI_BASE_URL}/models`.
Any OpenAI-compatible vendor works (Z.ai/GLM, OpenAI, Groq, Together, a
self-hosted vLLM), so you are not locked in.

Verify after deploy:

```bash
curl -s https://<api-host>/api/v1/tutor/status
```

Expected: `available: true`, `provider: "openai"`, your model name. If it says
the model is unavailable, `OPENAI_MODEL` does not match an id the provider
serves; the message lists ids it found. If the key is missing, startup logged a
warning and sends return `503 ai_unavailable`.

Keep keys server-side only. `VITE_` variables are inlined into the browser bundle.

---

## 4. Email

See `docs/RUNBOOK.md` §6. At minimum, verify the sending domain (SPF/DKIM/DMARC)
with the provider before inviting users; otherwise verification and reset mail
lands in spam.

---

## 5. Post-deploy checklist

```bash
curl -fsS https://<api-host>/api/v1/health          # status ok, database ok; 503 if the DB is down
curl -s  https://<api-host>/api/v1/tutor/status     # available true
```

Then, in the browser on the static site:

1. Register a new account — the verification email arrives.
2. Complete onboarding and open the dashboard (data comes from the API).
3. Send a tutor message — a model reply is stored and shown with its provider
   label.
4. Run a mock interview and finish it — XP and the `interview_ready` achievement
   appear.
5. Request a password reset, follow the link, sign in with the new password.

Known production caveats (also in `docs/SECURITY.md`):

* Rate limiting is per process; with several instances, move the counter to Redis.
* Access tokens stay valid until they expire after a password change.
* Phase 4 code execution is still blocked; no student code runs anywhere.
