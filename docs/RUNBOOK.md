# Operations runbook

Everything here is written for the deployment described in `README.md`: a FastAPI
process behind a reverse proxy with PostgreSQL, a Vite-built frontend, and
and a hosted OpenAI-compatible model provider. Development on SQLite is not a deployment.

---

## 1. Pre-flight checklist

| Item | Requirement |
| --- | --- |
| `ENVIRONMENT` | `production` — the app refuses to start with unsafe configuration |
| `SECRET_KEY` | ≥32 random characters, unique per environment |
| `DATABASE_URL` | `postgresql+asyncpg://…` (SQLite is rejected in production) |
| `COOKIE_SECURE` | `true`, served over HTTPS |
| `FRONTEND_ORIGIN` | exact public origin, no trailing slash |
| `ADDITIONAL_ORIGINS` | JSON list of any extra trusted origins |
| `APP_BASE_URL` | `https://…` — used in verification and reset links |
| `RATE_LIMIT_ENABLED` | `true` |
| `EMAIL_DELIVERY` | see §6; the default `console` is development-only |
| `AI_PROVIDER` | `openai` with `OPENAI_*` set, or `disabled` |

Startup fails fast when a production requirement is violated:
`SECRET_KEY`, `COOKIE_SECURE`, PostgreSQL, `APP_BASE_URL` and rate limiting are
all validated.

---

## 2. Deploy

```bash
git pull
docker compose build
docker compose up -d
docker compose logs -f api
```

The API container runs migrations and seeds on start (`python -m app.cli init`).
Seeding is idempotent: subjects, achievements, curriculum, career roles and the
interview question bank are inserted or refreshed, never duplicated.

Verify:

```bash
curl -fsS https://api.example.com/api/v1/health
```

`status` must be `ok`; `database` must be `ok`. The endpoint answers **503** with
`status: degraded` when the database is unreachable, so a platform health check
(`${PORT}`, Render, an ALB target group) stops sending traffic to that instance.
Check the connection string and the database service before restarting the API.

---

## 3. Migrations

```bash
cd backend
./.venv/Scripts/python.exe -m app.cli init    # upgrade to head + seed
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe -m alembic downgrade -1
./.venv/Scripts/python.exe -m alembic current
```

Migration order (each revision has a tested `downgrade`):

| Revision | Scope |
| --- | --- |
| `1cbd9fa10ad8` | initial schema |
| `38d689103031` | curriculum module metadata |
| `9f2c1a7b4e10` | tutor conversations |
| `c3d4e5f6a7b8` | career roles, interviews, resume claims |
| `d4e5f6a7b8c9` | lockout columns, email tokens, index review |

Rollback rule: take a backup **before** downgrading, and only downgrade one
revision at a time while the API is stopped. New columns and tables are additive,
but a downgrade drops their data permanently.

---

## 4. Backup and restore (PostgreSQL)

```bash
# nightly logical backup, keep 14 days
pg_dump --format=custom --no-owner --file=attestive-$(date +%F).dump "$DATABASE_URL"

# restore into an empty database
createdb attestive_restore
pg_restore --no-owner --dbname=attestive_restore attestive-$(date +%F).dump
```

Restore drill (quarterly): restore yesterday's dump into a scratch database, run
`python -m app.cli init` against it (no-op if already current), then start one
API instance pointed at the scratch database and check `/api/v1/health` and a
sign-in. A backup that has never been restored is not a backup.

Retention: 14 daily, 8 weekly, 12 monthly. Store them encrypted and outside the
database host.

---

## 5. Authentication operations

* **Lockout** — five failed passwords lock an account for 15 minutes
  (`MAX_FAILED_LOGINS`, `LOCKOUT_MINUTES`). The response is `423 account_locked`
  with the minutes remaining. A successful sign-in or a password reset clears it.
* **Unlock a user immediately** — either ask them to use password reset, or:

  ```sql
  UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE email = '…';
  ```

* **Refresh tokens** are stored hashed and rotated on every use. Replaying a
  rotated token revokes every session for that user.
* **Password reset** revokes all refresh tokens and clears lockout. Access tokens
  already issued remain valid until they expire (30 minutes by default), which is
  the documented trade-off of stateless access tokens.

---

## 6. Email delivery

`EMAIL_DELIVERY` selects the transport:

| Value | Behaviour | Needs |
| --- | --- | --- |
| `console` (default) | Logs the full message in development. Outside development the body is suppressed so a reset link never lands in a production log. | — |
| `disabled` | Creates the token but delivers nothing, and says so. | — |
| `resend` | `POST https://api.resend.com/emails` | `EMAIL_API_KEY`, verified sender in `EMAIL_FROM` |
| `sendgrid` | `POST https://api.sendgrid.com/v3/mail/send` | `EMAIL_API_KEY`, verified sender in `EMAIL_FROM` |
| `smtp` | stdlib SMTP with optional STARTTLS (SES, Mailgun, Postmark SMTP, Gmail app password) | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_STARTTLS` |

Setup:

1. Verify the sending domain at the provider (SPF, DKIM, and a DMARC record).
2. Set `EMAIL_FROM` to an address on that domain, e.g.
   `Attestive <no-reply@mail.example.com>`.
3. Put the credential in the environment (or the platform's secret store) as
   `EMAIL_API_KEY` / `SMTP_PASSWORD`. Never commit it and never paste it into a
   ticket.
4. Set `EMAIL_DELIVERY` and restart the API. Startup logs a warning while the
   transport is still `console` outside development.
5. Send a real signup and a real reset, and confirm both arrive and that the
   links open the frontend on `APP_BASE_URL`.

Delivery failures are logged with the provider's status and response body and
are never reported as a successful send; registration and reset requests still
succeed so a mail outage cannot lock users out of the app.

Verification links expire after 48 hours; reset links after 60 minutes. Both are
single-use.

---

## 7. Rate limiting

`RateLimitMiddleware` keeps a per-process sliding window (60 s):

* auth endpoints: `RATE_LIMIT_AUTH_PER_MINUTE` (default 20)
* everything else: `RATE_LIMIT_DEFAULT_PER_MINUTE` (default 120)
* health checks are exempt

The limiter keys on `request.client.host`, so the API must sit behind a proxy
that sets `X-Forwarded-For` **and** trust it: `uvicorn --proxy-headers
--forwarded-allow-ips=*` (already the container command). Without it every
request appears to come from the proxy and all users share one bucket.

**Limitation:** counters are in memory per worker. With multiple instances or
workers each has its own budget, and a restart resets it. For a multi-instance
deployment move the counter to Redis (or the reverse proxy) and keep the same
response envelope (`429`, `rate_limited`, `Retry-After`).

If legitimate users hit the limit, raise the value rather than disabling the
middleware — production configuration validation refuses to start with rate
limiting disabled.

---

## 8. AI model versioning

* `AI_PROVIDER` selects the path: `openai` for any hosted OpenAI-compatible API,
  `disabled` for deterministic-only (the tutor then reports unavailable).
* `OPENAI_BASE_URL`, `OPENAI_MODEL` and `OPENAI_API_KEY` configure the provider.
  The key stays server-side; never expose it through a `VITE_` variable.
* `OPENAI_MODEL` names the model used by the tutor and (when enabled) roadmap
  notes. Changing it changes behaviour; treat it as a deployment change and
  re-run the evaluation below.
* `GET /api/v1/tutor/status` reports the provider, the configured model, whether
  it is installed, and the exact problem when it is not.
* When the model is missing or unreachable, tutor sends return
  `503 ai_unavailable` and store nothing. Roadmaps fall back to a deterministic
  rationale, and `learning_paths.generated_by` records `deterministic`.
* Evaluation before changing models: run the tutor manually on five prompts
  (explain, four hint levels, worked example, check-me) for one subject, check
  that hints never reveal the final solution, and confirm replies are grounded in
  the cited curriculum modules. Record the model name and date in the change log.

---

## 9. Load and performance checks

```bash
python scripts/load_test.py --base-url https://api.example.com --requests 200 --concurrency 20
```

The script reports ok/fail counts and p50/p95/p99 latency for `GET /health` and
`GET /catalog/subjects`. Run it against staging, not production, and compare runs
only on the same hardware.

Index review already in place: `learning_activities(user_id, occurred_on)`,
`assessment_attempts(user_id, status, completed_at)`,
`xp_transactions(user_id, created_at)`, `mock_interviews(user_id, started_at)`,
`email_tokens(user_id, purpose)`. Use `EXPLAIN ANALYZE` on the analytics and
dashboard queries after a data-volume change before adding more.

Caching: only the public catalogue is cacheable (`Cache-Control: public,
max-age=300`). Every authenticated response is per-user and must not be cached by
a shared proxy.

---

## 10. Incident triage

| Symptom | First checks |
| --- | --- |
| `degraded` health | database reachable, connection pool exhausted, migrations applied |
| 500s after deploy | `docker compose logs api`; run `alembic current`; check the newest migration |
| users cannot sign in | lockout (`locked_until`), clock skew, `SECRET_KEY` changed (invalidates tokens) |
| everyone gets 429 | one client is looping; inspect the reverse-proxy log by IP |
| tutor answers 503 | `OPENAI_BASE_URL`, `OPENAI_MODEL`, `OPENAI_API_KEY`; check `GET /api/v1/tutor/status` |
| links in emails do not work | `APP_BASE_URL` must match the public frontend origin exactly |
