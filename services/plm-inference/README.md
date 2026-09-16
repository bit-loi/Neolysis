# Neolysis PLM Inference Service

Dedicated microservice that owns the ESM2 protein-language-model lifecycle. The
primary `neolysis-backend` FastAPI app never loads this model in-process; it
calls this service over HTTP through `app.services.embeddings.RemotePLMProvider`.

## Status

This service was authored but **not started or live-tested** in the session
that created it, by explicit request (low-resource development constraints:
no model downloads, no heavy installs, no background processes). Its request/
response contract is covered by mocked unit tests in `neolysis-backend/tests/`.

## Model

Default: `facebook/esm2_t30_150M_UR50D` (150M parameters — a reasonable balance
for a serious MVP). Configurable via `PLM_MODEL`. Smaller (`esm2_t12_35M_UR50D`)
is a good choice for lightweight local development; `esm2_t33_650M_UR50D` is an
optional, substantially heavier upgrade — only enable it if you have the
memory/compute budget.

## Running it (separate environment from neolysis-backend)

```
cd services/plm-inference
python -m venv venv
./venv/Scripts/activate   # Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8100
```

First startup downloads the model from Hugging Face (public checkpoint, no
`HF_TOKEN` required) and loads it once. Subsequent requests reuse the loaded
model — it is not reloaded per request.

## Wiring it into the main backend

In `neolysis-backend/.env`:

```
PROTEIN_EMBEDDING_MODE=esm2
PLM_SERVICE_URL=http://localhost:8100
PLM_MODEL=facebook/esm2_t30_150M_UR50D
```

If `PLM_SERVICE_URL` is unset, or this service is unreachable, or a request
fails for any reason, `neolysis-backend` falls back to its lightweight baseline
embedding and marks the result `status="fallback"` with an explicit
`fallback_reason` — it never silently pretends to be an ESM2 embedding.

## API

`POST /embed`

```json
{ "sequence": "MKT...", "pooling": "mean" }
```

```json
{
  "sequence_sha256": "...",
  "model": "facebook/esm2_t30_150M_UR50D",
  "model_revision": null,
  "embedding_dimension": 640,
  "pooling": "mean",
  "cache_hit": false,
  "embedding": [...]
}
```

Sequences longer than `PLM_MAX_RESIDUES` (default 1022, the practical ESM2
context limit) are rejected with HTTP 422 rather than silently truncated.

`GET /health` reports whether the model has finished loading.
