# Security baseline

This documents what is implemented, what is assumed, and what is still missing.
It is a working baseline, not a certification.

---

## 1. Implemented controls

| Area | Control |
| --- | --- |
| Passwords | Argon2id via `pwdlib`, minimum length + letters/numbers, rehash on login when parameters change, reuse rejected on change/reset |
| Sessions | 30-minute JWT access tokens held in memory; 14-day refresh tokens stored **hashed**, rotated on every use, replay revokes all sessions |
| Cookies | refresh cookie is `HttpOnly`, `SameSite=Lax`, path-scoped to `/api/v1/auth`, `Secure` in production |
| Origin checks | cookie endpoints reject foreign `Origin` headers, not just foreign CORS requests |
| Account lockout | 5 failed passwords → 15-minute lock (`423 account_locked`), cleared on success or reset |
| Rate limiting | per-process sliding window, tighter budget on `/auth/*`, health exempt, `429` + `Retry-After` |
| Enumerations | login and password reset return identical responses for unknown and known addresses |
| Email tokens | verification (48 h) and reset (60 min) tokens stored as SHA-256 fingerprints, single-use, expiry enforced |
| Authorisation | every attempt, conversation, roadmap, interview and resume claim is scoped to `user.id`; other users receive `404` |
| Input validation | Pydantic schemas on every request body; SQL through SQLAlchemy bound parameters |
| Secrets | environment/`.env` only, `.env` gitignored, no secrets in the frontend bundle |
| Headers | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy`, COOP, HSTS when `COOKIE_SECURE` |
| CSP | API responses: `default-src 'none'; frame-ancestors 'none'; base-uri 'none'` (docs UI excluded) |
| Unhandled errors | one envelope, generic message, details logged server-side only |
| Production config | startup refuses unsafe `SECRET_KEY`, insecure cookies, SQLite, non-HTTPS `APP_BASE_URL`, disabled rate limiting |

## 2. Assumptions

* TLS terminates at a reverse proxy; the app never sees plaintext production
  traffic and trusts `X-Forwarded-*` only through that proxy.
* The database is not exposed publicly.
* One process per container. The rate limiter and lockout counters are process
  local (lockout state lives in the database and is shared).
* No untrusted code is executed. The Phase 4 coding lab stays blocked until a
  separate runner exists (ADR-007); nothing in the API runs student code.

## 3. Scanning (run before each release)

```bash
# Python dependencies
cd backend && ./.venv/Scripts/python.exe -m pip install pip-audit && \
  ./.venv/Scripts/python.exe -m pip_audit -r requirements.txt

# Frontend dependencies
cd frontend && npm audit --omit=dev

# Container image
docker scout cves attestive-api:latest    # or: trivy image attestive-api:latest

# Static checks
cd backend && ./.venv/Scripts/python.exe -m ruff check app tests
```

CI runs lint, compile, migrations + seed, the backend suite, frontend typecheck
and the production build on every push. Dependency and image scanning are manual
because they need registry/network access; record the result in the release notes.

## 4. Secrets review

* `SECRET_KEY` rotates deliberately: all access and refresh tokens become invalid,
  so every user signs in again. Plan it as a maintenance window.
* AI and database credentials belong in the environment, never in the repo, logs
  or the frontend.
* `EMAIL_DELIVERY=console` logs verification and reset links in development only;
  outside development the body is suppressed. Production must use `resend`,
  `sendgrid` or `smtp`, and startup validates that the credentials exist.
* Provider API keys live in the environment/secret store. Rotate a key
  immediately if it appears in a log, a screenshot or a support thread.
* Rotate any credential that has ever been pasted into a chat, ticket or log.

## 5. Known gaps (deliberate, documented)

1. **No email provider is configured in this repository.** Transports for
   Resend, SendGrid and SMTP are implemented in `core/mailer.py`, but delivering
   mail requires the operator to set `EMAIL_DELIVERY`, a verified sender and a
   credential. Until then the console transport suppresses message bodies outside
   development rather than logging reset links.
2. **Rate limiting is per process and in memory.** Multi-instance deployments
   need a shared counter.
3. **No MFA / TOTP.** Not implemented.
4. **Access tokens are not revoked on password change or reset.** They expire
   within 30 minutes; refresh tokens are revoked immediately.
5. **No CSRF token on cookie endpoints.** Mitigated by `SameSite=Lax` plus an
   origin allowlist; a strict token-based CSRF scheme is not in place.
6. **No automated dependency scanning in CI** (manual commands above).
7. **No WAF, bot protection or IP reputation.**
8. **Audit logging is request-level only.** Administrative actions do not have a
   separate immutable audit trail.

## 6. Reporting

Security issues should go to the project owner privately, with reproduction
steps and the affected endpoint or revision. Do not open a public issue for an
unfixed vulnerability.
