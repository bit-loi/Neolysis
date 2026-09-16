from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EmbedRequest(BaseModel):
    sequence: str = Field(..., min_length=1, description="Raw amino-acid sequence (no FASTA header).")
    pooling: str = Field("mean", description="Pooling strategy. Only 'mean' is currently implemented.")


class EmbedResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sequence_sha256: str
    model: str
    model_revision: Optional[str] = None
    embedding_dimension: int
    pooling: str
    cache_hit: bool = False
    embedding: List[float]
