from typing import Any, Optional

from app.config import settings
from app.schemas.enzyme import EmbeddingResult
from app.services.protein_features import AMINO_ACIDS


class ProteinEmbeddingService:
    """Training-free protein embedding with an explicit, observable fallback path."""

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or settings.PROTEIN_EMBEDDING_MODE).lower()
        self._tokenizer: Any = None
        self._model: Any = None

    def generate_embedding(self, sequence: str) -> EmbeddingResult:
        if self.mode == "esm2":
            try:
                return self._generate_esm2(sequence)
            except Exception as exc:
                return self._generate_baseline(
                    sequence,
                    fallback_reason=f"ESM2 inference unavailable: {type(exc).__name__}: {exc}",
                )
        return self._generate_baseline(sequence)

    def _generate_baseline(
        self, sequence: str, fallback_reason: Optional[str] = None
    ) -> EmbeddingResult:
        length = max(len(sequence), 1)
        composition_vector = [round(sequence.count(aa) / length, 6) for aa in AMINO_ACIDS]
        grouped = [
            sum(sequence.count(aa) for aa in "AVLIMFWY") / length,
            sum(sequence.count(aa) for aa in "DE") / length,
            sum(sequence.count(aa) for aa in "KRH") / length,
            sum(sequence.count(aa) for aa in "STNQ") / length,
            sum(sequence.count(aa) for aa in "CGP") / length,
        ]
        vector = composition_vector + [round(value, 6) for value in grouped]
        return EmbeddingResult(
            vector=vector,
            dimensions=len(vector),
            mode="baseline",
            model_version="baseline-composition-v0.1",
            provider="neolysis",
            status="fallback" if fallback_reason else "completed",
            fallback_reason=fallback_reason,
            limitations=[
                "This is a lightweight baseline embedding for staging, not a trained protein language model embedding."
            ],
        )

    def _generate_esm2(self, sequence: str) -> EmbeddingResult:
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("install the optional 'transformers' dependency") from exc

        if self._tokenizer is None or self._model is None:
            self._tokenizer = AutoTokenizer.from_pretrained(settings.PROTEIN_EMBEDDING_MODEL)
            self._model = AutoModel.from_pretrained(settings.PROTEIN_EMBEDDING_MODEL)
            self._model.eval()

        max_residues = settings.PROTEIN_EMBEDDING_MAX_RESIDUES
        model_sequence = sequence[:max_residues]
        tokens = self._tokenizer(model_sequence, return_tensors="pt", add_special_tokens=True)
        with torch.no_grad():
            output = self._model(**tokens).last_hidden_state

        # Exclude ESM beginning/end special tokens before mean pooling residues.
        pooled = output[0, 1 : len(model_sequence) + 1].mean(dim=0)
        vector = [round(float(value), 6) for value in pooled.tolist()]
        limitations = [
            "A pretrained representation is not itself a calibrated enzyme-function classifier.",
            "Downstream conclusions still require database, structural, and wet-lab validation.",
        ]
        if len(sequence) > max_residues:
            limitations.append(
                f"Sequence was truncated from {len(sequence)} to {max_residues} residues for embedding inference."
            )
        return EmbeddingResult(
            vector=vector,
            dimensions=len(vector),
            mode="pretrained",
            model_version=settings.PROTEIN_EMBEDDING_MODEL,
            provider="Hugging Face Transformers / Meta ESM",
            status="completed",
            limitations=limitations,
        )


protein_embedding_service = ProteinEmbeddingService()
