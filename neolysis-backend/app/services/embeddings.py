from app.schemas.enzyme import EmbeddingResult
from app.services.protein_features import AMINO_ACIDS


class ProteinEmbeddingService:
    def __init__(self, mode: str = "baseline"):
        self.mode = mode

    def generate_embedding(self, sequence: str) -> EmbeddingResult:
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
            mode=self.mode,
            model_version="baseline-composition-v0.1",
            limitations=[
                "This is a lightweight baseline embedding for staging, not a trained protein language model embedding."
            ],
        )


protein_embedding_service = ProteinEmbeddingService()
