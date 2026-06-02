# Neolysis - Enzyme Engineering Platform for Industrial Biotechnology

Neolysis is a computational enzyme intelligence platform that helps biotech and industrial R&D teams analyze enzyme sequences, estimate relevant properties, prioritize variants, and plan wet-lab validation.

This staging version pivots Neolysis away from drug discovery and toward enzyme engineering for industrial biotechnology.

## What It Does

- FASTA upload and raw protein sequence input
- Protein sequence validation
- Basic protein feature extraction
- Enzyme function prediction scaffold
- Industrial property scoring scaffold
- Variant ranking
- Mutation risk analysis
- Agentic report generation
- Wet-lab validation planning

## What It Is Not

- Not a guarantee of better enzymes
- Not a replacement for wet-lab validation
- Not experimental proof of activity
- Not a fully automated final enzyme design platform

All outputs are computational estimates intended for candidate prioritization. Experimental wet-lab validation is required before industrial use.

## Core Workflow

```text
Upload enzyme FASTA
-> validate sequence
-> extract protein features
-> generate baseline embedding
-> predict enzyme family/function scaffold
-> score industrial property fit
-> rank candidate variants
-> analyze mutation risk
-> generate validation planning report
```

## Target Use Cases

- Alkaline proteases for detergent conditions
- Thermostable cellulases for biomass degradation
- Lipases for food processing
- Amylases for starch processing
- Laccases for textile or environmental processing
- Academic protein engineering research

## Active Backend API

The FastAPI staging API focuses on enzyme engineering:

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Liveness probe |
| `POST /api/v1/sequences/validate` | Validate FASTA or raw protein sequence |
| `POST /api/v1/sequences/features` | Extract protein sequence features |
| `POST /api/v1/enzymes/predict-function` | Baseline enzyme function prediction |
| `POST /api/v1/properties/score` | Baseline industrial property scoring |
| `POST /api/v1/variants/rank` | Rank candidate variants |
| `POST /api/v1/variants/risk` | Analyze mutation risk |
| `POST /api/v1/agents/analyze` | Run tool-using agentic workflow |
| `POST /api/v1/reports/generate` | Generate structured report |

## Frontend Routes

| Route | Purpose |
| --- | --- |
| `/` | Enzyme engineering landing page |
| `/analyze` | Sequence analysis and report workflow |
| `/variants` | Variant ranking interface |
| `/agent-report` | Agentic report interface |
| `/methodology` | Scientific method and limitations |
| `/about` | Product positioning |
| `/experimental/md-sandbox` | Optional experimental Rust/WASM molecular dynamics sandbox |

Legacy drug-discovery routes are no longer linked from the active UI. Direct visits to old target and compound pages redirect to `/analyze`.

The MD sandbox route is disabled unless `NEXT_PUBLIC_ENABLE_MD_ENGINE=true` is set. It is a simplified browser-based simulation sandbox for future structure-aware enzyme engineering, not a validated protein dynamics engine and not part of the core enzyme scoring workflow.

## Tech Stack

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- 3Dmol.js optional
- Experimental Rust/WASM molecular dynamics sandbox optional

### Backend

- FastAPI
- Pydantic schemas
- Biopython feature extraction when available
- PostgreSQL or SQLite-compatible staging direction
- Redis/Celery optional for future background workflows
- Docker-ready project layout

### Bioinformatics / ML Direction

- Protein feature extraction
- Protein embedding service abstraction
- Baseline scoring for staging
- Future PyTorch, Hugging Face, XGBoost, or structure-aware integration

### Agentic System

The agent is a tool-using scientific workflow coordinator. It calls deterministic and baseline computational tools, records its tool calls, and generates a report from structured outputs.

Agent modules:

- Sequence analyst
- Enzyme function analyst
- Industrial fit analyst
- Variant prioritization analyst
- Report generator

The agent does not invent final enzyme designs or claim experimental activity.

## Development

### Backend

```bash
cd neolysis-backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Run staging tests:

```bash
cd neolysis-backend
python -m pytest
```

### Frontend

```bash
cd neolysis-frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## CI/CD

GitHub Actions automation lives in `.github/workflows/ci.yaml`.

The workflow runs on pushes and pull requests for `main`, `staging`, and `develop`:

- backend staging API tests
- frontend lint and production build
- Rust/WASM formatting and WASM build check

Staging deployment is triggered only on pushes to the `staging` branch after all checks pass. Add a repository or environment secret named `STAGING_DEPLOY_WEBHOOK_URL` to connect the workflow to a staging host such as Render, Railway, Fly.io, or another deploy webhook provider. If the secret is not configured, the workflow keeps CI active and safely skips deployment.

## Staging Limitations

- Function prediction is a baseline scaffold, not a trained enzyme classifier.
- Property scores are transparent sequence-level proxies.
- Variant rankings are prioritization signals, not measured improvements.
- Wet-lab validation is required before industrial use.
- The WASM molecular dynamics sandbox is optional, experimental, and not required for the core sequence intelligence MVP.
