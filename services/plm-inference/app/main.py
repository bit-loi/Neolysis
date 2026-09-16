"""
Neolysis — Protein Language Model (PLM) Inference Microservice
=================================================================
Dedicated FastAPI service that owns the ESM2 model lifecycle.

The primary Neolysis backend must NEVER load a protein language model in its own
process. It reaches ESM2 only through this service's /embed endpoint, via
neolysis-backend's app.services.embeddings.RemotePLMProvider.

Run (only when torch/transformers are installed in this service's own environment,
separate from neolysis-backend's venv):

    pip install -r requirements.txt
    uvicorn app.main:app --host 0.0.0.0 --port 8100

The model is loaded exactly once at startup via the FastAPI lifespan, not per-request.
"""
import hashlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from loguru import logger

from app.config import settings
from app.schemas import EmbedRequest, EmbedResponse

_model_state: dict = {"tokenizer": None, "model": None, "device": None, "revision": None}


def _resolve_device(preference: str) -> str:
    if preference in {"cpu", "cuda"}:
        return preference
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from transformers import AutoModel, AutoTokenizer

    device = _resolve_device(settings.PLM_DEVICE)
    logger.info(f"Loading PLM model={settings.PLM_MODEL} device={device} (once, at startup)")
    tokenizer = AutoTokenizer.from_pretrained(settings.PLM_MODEL, token=settings.HF_TOKEN)
    model = AutoModel.from_pretrained(settings.PLM_MODEL, token=settings.HF_TOKEN)
    model.eval()
    model.to(device)
    _model_state["tokenizer"] = tokenizer
    _model_state["model"] = model
    _model_state["device"] = device
    _model_state["revision"] = getattr(model.config, "_commit_hash", None)
    logger.info("PLM model loaded and ready.")
    try:
        yield
    finally:
        _model_state["tokenizer"] = None
        _model_state["model"] = None
        logger.info("PLM model unloaded.")


app = FastAPI(
    title="Neolysis PLM Inference Service",
    version="0.1.0",
    description=(
        "Internal microservice. Not exposed to the browser. Called only by the "
        "primary Neolysis backend's RemotePLMProvider."
    ),
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    loaded = _model_state["model"] is not None
    return {
        "status": "healthy" if loaded else "loading",
        "model": settings.PLM_MODEL,
        "device": _model_state["device"],
    }


@app.post("/embed", response_model=EmbedResponse)
async def embed(payload: EmbedRequest) -> EmbedResponse:
    import torch

    from app.pooling import mean_pool_residues

    if payload.pooling != "mean":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported pooling strategy '{payload.pooling}'; only 'mean' is implemented.",
        )

    sequence = payload.sequence.strip().upper()
    if not sequence:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty sequence.")

    # Never silently truncate. Reject explicitly and tell the caller why.
    if len(sequence) > settings.PLM_MAX_RESIDUES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Sequence length {len(sequence)} exceeds PLM_MAX_RESIDUES="
                f"{settings.PLM_MAX_RESIDUES}. This service does not truncate sequences; "
                "shorten the input or implement an explicit chunking strategy upstream."
            ),
        )

    tokenizer = _model_state["tokenizer"]
    model = _model_state["model"]
    if tokenizer is None or model is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model is still loading.")

    sequence_sha256 = hashlib.sha256(sequence.encode("utf-8")).hexdigest()
    device = _model_state["device"]

    tokens = tokenizer(sequence, return_tensors="pt", add_special_tokens=True)
    tokens = {key: value.to(device) for key, value in tokens.items()}

    with torch.inference_mode():
        output = model(**tokens)
    hidden = output.last_hidden_state  # (1, seq_len, hidden_dim)

    pooled = mean_pool_residues(hidden, tokens["attention_mask"])
    embedding_vector = pooled[0].detach().cpu().float().tolist()

    # Provenance/log only the hash prefix and length — never the full sequence.
    logger.info(
        f"embed model={settings.PLM_MODEL} sha256={sequence_sha256[:12]} "
        f"length={len(sequence)} dim={len(embedding_vector)}"
    )

    return EmbedResponse(
        sequence_sha256=sequence_sha256,
        model=settings.PLM_MODEL,
        model_revision=_model_state["revision"],
        embedding_dimension=len(embedding_vector),
        pooling="mean",
        cache_hit=False,
        embedding=embedding_vector,
    )
