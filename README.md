# Aegis Autonomous Security Auditing & Compliance Engine

An agentic security-auditing portfolio application that accepts a public repository URL or pasted source payload, runs dependency/CVE, secret, and policy checks, then exposes auditable remediation diffs through a Next.js command-center dashboard.

> Security note: this project intentionally performs **safe, content-based analysis**. It does not clone arbitrary repositories, execute target code, apply patches automatically, or expose discovered secrets in UI telemetry.

## Architecture

```text
┌────────────────────────────────────────────────────────────────┐
│ Next.js 14 Dashboard (App Router, Tailwind, Recharts)           │
│  Repo target → live telemetry → findings → reviewer-approved diff│
└───────────────────────────────┬────────────────────────────────┘
                                │ /api rewrite
┌───────────────────────────────▼────────────────────────────────┐
│ FastAPI API                                                      │
│ POST audit-repo → asyncio task → GET audit-status/{job_id}      │
└───────────────────────────────┬────────────────────────────────┘
                                │
┌───────────────────────────────▼────────────────────────────────┐
│ SecurityEngine                                                    │
│ Auditor: dependency parser + advisory map + secret regex + policy │
│ Remediation: deterministic, reviewable unified-diff generation    │
└────────────────────────────────────────────────────────────────┘
```

## Features

- Responsive security command center with posture score, severity metrics, charts, telemetry, and diff review.
- AsyncIO-backed non-blocking audit jobs, suitable for replacing with Redis/Celery or a cloud queue in production.
- Dependency checks for selected npm and PyPI packages with version-aware local advisory fallback.
- Safe NVD connectivity probe. The scanner still functions when NVD is unavailable.
- Secret patterns for AWS keys, GitHub tokens, private-key headers, and generic credential assignments; findings redact visible evidence.
- OWASP-aligned policy detection for non-local HTTP usage and `eval()` calls.
- Reviewer-controlled patch proposals. “Apply Fix” queues a front-end-only approval state; it never mutates source code.
- Fully interactive mock fallback when the API is unreachable.

## Local setup

Prerequisites: Node.js 20+, Python 3.11+, and npm.

```bash
git clone https://github.com/YOUR_ORG/autonomous-security-auditing-compliance-engine.git
cd autonomous-security-auditing-compliance-engine
npm install
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
npm run dev
```

Open `http://localhost:3000`. The web app runs on port 3000; FastAPI runs on port 8000.

### Docker

```bash
docker compose up --build
```

## API specification

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Returns API, agent-engine, NVD connectivity, and active-job status |
| `POST` | `/api/v1/audit-repo` | Queues an audit using `repository_url` or `code_payload` |
| `GET` | `/api/v1/audit-status/{job_id}` | Returns job status, telemetry, findings, score, and patches |
| `POST` | `/api/v1/generate-patch` | Returns a safe remediation diff for a finding ID |

Example audit:

```bash
curl -X POST http://localhost:8000/api/v1/audit-repo \
  -H 'Content-Type: application/json' \
  -d '{"code_payload":"{\\"dependencies\\":{\\"lodash\\":\\"4.17.20\\"}}"}'
```

## Deployment

### Vercel frontend

Deploy the repository to Vercel and configure the `BACKEND_URL` environment variable with your Render FastAPI service URL. The `next.config.js` rewrite directs browser calls from `/api/*` to that backend.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_ORG/autonomous-security-auditing-compliance-engine)

### Render backend

Create a Render Web Service from this repository:

- Runtime: Docker, or Python 3.11
- Build command for Python runtime: `pip install -r backend/requirements.txt`
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Set `BACKEND_URL` in Vercel to the Render service base URL.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_ORG/autonomous-security-auditing-compliance-engine)

## Production hardening roadmap

For a real enterprise deployment, add authenticated Git provider access with explicit scopes, repository allowlists, per-tenant isolation, encrypted job persistence (PostgreSQL), Redis/Celery or managed queue workers, SBOM generation, OSV/NVD API-key-backed advisory resolution with caching, SAST/SCA tool integrations, signed patch branches, OIDC, rate limits, audit log retention, and human approval gates before every Git write.
