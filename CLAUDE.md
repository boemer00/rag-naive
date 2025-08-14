# Longevity Insights Platform — Audit, Architecture, and Phased Plan

This document captures the audit and the exact plan to build a streamlined longevity insights platform that integrates multiple device metrics into a unified view.

Target devices: Apple Watch, Garmin, Oura, Whoop.
Core metrics: Heart Rate Variability (HRV), VO₂ Max / Cardiorespiratory Fitness, Sleep Quality & Architecture.

---

## 1) Project audit

### Strengths
- RAG core with Chroma and OpenAI; clean helpers and web API endpoints for `/query`, `/assistant/message`, `/health-analysis`.
- Agent scaffold with semantic/filtered retries and compact, explainable trace.
- Apple Health XML parsing and aggregation for resting HR, VO₂ max, and sleep duration with RAG context integration.
- Minimal frontend providing forms for querying and Apple Health uploads.

### Gaps vs goal
- No direct integrations for Garmin, Oura, Whoop (OAuth/webhooks missing). Apple Watch supported via manual XML only.
- No per-user time-series storage for biometrics; Chroma is for documents, not metrics.
- No cross-device standardization and calibration layer for HRV/VO₂ max/sleep.
- No auth/consent model, token storage, encryption-at-rest, or PHI policy.
- No insights rules/ML to generate proactive nudges; no WhatsApp integration.
- Frontend lacks device connection flows, charts, freshness/status indicators.

### Quick wins
- Introduce a health domain with clear schemas for HRV/VO₂/Sleep and daily summaries.
- Add a relational/time-series store (Postgres/TimescaleDB) and ETL jobs.
- Stub device connectors and run the end-to-end pipeline with mocked data before real OAuth.
- Choose canonical standards per metric and keep raw samples for traceability.

---

## 2) Phased plan

### Phase 1 — Web dashboard (MVP)
Goal: Users connect devices (or upload Apple XML) and view standardized metrics and basic insights.

- Backend
  - Add auth (JWT + cookies) and user profiles.
  - Device routes: `/devices/connect/{provider}`, `/devices/callback/{provider}`, `/devices/status`.
  - Metrics routes: `/metrics/normalized?metric=hrv_rmssd&range=30d`, `/summaries/daily`, `/insights/latest`.
  - Keep existing `/query`, `/assistant/message`, `/health-analysis` endpoints.
- Frontend
  - “Connect device” cards (Apple XML upload, Garmin, Oura, Whoop placeholders), connection status, last sync.
  - Three charts: HRV, VO₂ max, Sleep; 7/30/90-day ranges; data freshness badges.
  - Insights feed with basic rules (e.g., HRV 7-day drop > 20%).
- Data
  - Postgres (or TimescaleDB) for per-user time-series and summaries.
  - ETL jobs to backfill/poll data until webhooks are enabled.

### Phase 2 — Standardize the data
Goal: Pick a reference standard per metric and normalize all devices to it with conversion/calibration.

- HRV
  - Canonical: RMSSD (ms). Many devices (Oura/Whoop) expose RMSSD; Apple often provides SDNN.
  - Avoid global SDNN→RMSSD conversions; prefer storing both and learning per-user, per-device calibration (offset/scale) using overlapping windows.
- VO₂ max
  - Canonical: mL/kg/min. Prefer Garmin (Firstbeat) as reference where available; Apple “Cardio Fitness” as secondary.
  - For devices lacking VO₂ max, provide an estimator (HR + pace + demographics) with provenance flags.
- Sleep
  - Canonical outputs: total sleep time, efficiency, stages (N1/N2/N3/REM), latency, WASO.
  - Compute a transparent unified 0–100 sleep score with adjustable weights (age/sex aware).
- Calibration service
  - Store per-user/device calibration parameters and model version; periodically re-fit using overlaps; guardrails (min samples and drift checks).

### Phase 3 — WhatsApp for nudges and quick insights
Goal: Send personalized nudges, reminders, and insights via WhatsApp before building a full app.

- Use WhatsApp Cloud API (Meta) or Twilio WhatsApp.
- Messaging service: templated nudges, quiet hours, throttling, audit logging, and user preferences.
- Trigger rules from the insights engine (e.g., HRV drop with poor sleep) and allow ad-hoc messages from the dashboard.

---

## 3) Architecture overview

### Data models (storage layer)
- User: `id`, `email`, `hashed_password`, `created_at`.
- DeviceAccount: `id`, `user_id`, `provider` in {apple_export, garmin, oura, whoop}, `access_token`, `refresh_token`, `scopes`, `expires_at`, `webhook_status`.
- RawSample: `id`, `user_id`, `provider`, `metric_type` in {hrv_rmssd, hrv_sdnn, vo2max, sleep_stage, sleep_score, hr_resting}, `value`, `unit`, `start_time`, `end_time`, `ingested_at`, `source_id`.
- NormalizedSample: `id`, `user_id`, `metric_type` in {hrv_rmssd, vo2max_mlkgmin, sleep_stage, sleep_score_0_100}, `value`, `unit`, `start_time`, `end_time`, `provenance`, `calibration_version`.
- DailySummary: per-day aggregates and rolling stats for dashboard.
- Insight: `id`, `user_id`, `kind`, `message`, `severity`, `created_at`, `evidence` (JSON).
- Nudge: `id`, `user_id`, `channel` (whatsapp), `template_id`, `payload`, `status`, `sent_at`, `error`.

### Modules and responsibilities
- `src/integrations/`
  - `base.py`: `DeviceConnector` interface: `get_oauth_authorize_url`, `exchange_code_for_token`, `refresh_token`, `fetch_metrics`, `handle_webhook`.
  - `garmin.py`, `oura.py`, `whoop.py`: provider-specific clients (start with mocks).
  - `apple.py`: XML upload path using existing Apple Health parser.
- `src/normalization/`
  - `schemas.py`: canonical enums and units.
  - `mapper.py`: `to_canonical(raw, user_context) -> list[NormalizedSample]`.
  - `calibration.py`: per-user/device parameter storage and re-fitting procedures.
  - `vo2max_estimator.py`: optional estimator when VO₂ max absent.
- `src/insights/`
  - `rules.py`: transparent, testable rules (e.g., HRV 7-day avg drop).
  - `generator.py`: convert streams → `Insight`s with evidence links.
- `src/messaging/`
  - `whatsapp.py`: send messages, verify webhooks, handle inbound.
  - `scheduler.py`: schedule nudges with user preferences and throttling.
- Backend (FastAPI)
  - Auth: `/auth/signup`, `/auth/login`, `/auth/me`.
  - Devices: `/devices/connect/{provider}`, `/devices/callback/{provider}`, `/devices/status`.
  - Metrics: `/metrics/normalized`, `/summaries/daily`.
  - Insights/Nudges: `/insights/latest`, `/nudges/test`.
  - RAG endpoints preserved as-is.
- Frontend
  - Dashboard with device connection cards, three key charts (HRV, VO₂ max, Sleep), freshness, and insights list with “Send via WhatsApp”.

### Storage and jobs
- Database: Postgres (consider TimescaleDB) with SQLAlchemy + Alembic.
- Jobs: `apscheduler` or `RQ/Celery` for polling, backfills, and calibration re-fits.
- Secrets: environment variables; encrypt PHI and tokens at rest.

### Privacy and security
- Consent per provider, audit logs, user data export/delete.
- Least-privilege scopes for device APIs; rotation and revocation flows.
- Clear data retention policies and user-facing privacy statements.

---

## 4) Environment and configuration
Suggested `.env` keys (examples; names may vary by provider):

```
# Core
OPENAI_API_KEY=
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db

# OAuth / device providers
GARMIN_CLIENT_ID=
GARMIN_CLIENT_SECRET=
OURA_CLIENT_ID=
OURA_CLIENT_SECRET=
WHOOP_CLIENT_ID=
WHOOP_CLIENT_SECRET=
OAUTH_REDIRECT_BASE_URL=https://your.domain

# WhatsApp
WHATSAPP_API_BASE=https://graph.facebook.com/v19.0
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_VERIFY_TOKEN=

# App
JWT_SECRET=
JWT_EXPIRES_MIN=60
```

---

## 5) Milestones and success metrics

- Phase 1 (Dashboard MVP): device connection stubs, charts, and basic insights live; ≥10 test users; <2 min full sync; p95 endpoint latency <500 ms (excluding provider fetch time).
- Phase 2 (Standardization): canonical metrics stored for all connected providers; calibration parameters learned for ≥70% of active users; backfill jobs stable.
- Phase 3 (WhatsApp): opt-in messaging enabled; rate limits and quiet hours enforced; ≥30% of insights delivered via nudges get user engagement.

---

## 6) Implementation workflow

We will follow a strict four-step workflow per feature/module:
1) Design (responsibility, public interface, data models, no code)
2) Scaffold (files and signatures, no logic)
3) Implement (working code with type hints; env-driven config; mocks for externals)
4) Test (pytest for all public interfaces and E2E flows)

This document aligns exactly with the current audit and the three-phase plan: build the dashboard, standardize metrics to canonical references, and integrate WhatsApp for engagement.


