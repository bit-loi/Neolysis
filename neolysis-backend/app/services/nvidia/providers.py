"""
Neolysis — NVIDIA Structure Providers
=========================================
Adapter implementations of the StructureProvider protocol, one per NVIDIA NIM
route. These call NvidiaNimClient.post() with the routes/payloads documented
by NVIDIA; they do not implement retry/backoff themselves (that lives in
NvidiaNimClient) and they do not decide which model to call for a given task
(that lives in StructureService's model-selection strategy).

IMPORTANT: only the protein-only payload shapes are implemented for
AlphaFold2/AlphaFold2 Multimer/OpenFold3/Boltz-2, matching the conceptual
schemas provided. Ligand/affinity payloads for Boltz-2 are NOT wired — the
brief explicitly requires inspecting NVIDIA's live schema before building
that, which cannot be done without network access to NVIDIA in this session.
predict_boltz2() raises NotImplementedError if ligands are supplied, rather
than guessing a field structure.
"""
from typing import Any, Dict, List, Optional, Protocol

from app.services.nvidia.client import NvidiaNimClient


class StructureProvider(Protocol):
    async def predict(self, sequences: List[str], **options: Any) -> Dict[str, Any]:
        ...


class NvidiaAlphaFold2Provider:
    PATH = "/v1/protein-structure/alphafold2/predict-structure-from-sequence"
    MODEL_LABEL = "alphafold2"

    def __init__(self, client: NvidiaNimClient):
        self._client = client

    async def predict(self, sequences: List[str], **options: Any) -> Dict[str, Any]:
        if len(sequences) != 1:
            raise ValueError("AlphaFold2 (monomer) requires exactly one sequence.")
        payload = {
            "sequence": sequences[0],
            "algorithm": options.get("algorithm", "mmseqs2"),
            "relax_prediction": options.get("relax_prediction", False),
        }
        return await self._client.post(
            self.PATH, payload, provider_label="nvidia", model_label=self.MODEL_LABEL
        )


class NvidiaAlphaFold2MultimerProvider:
    PATH = "/v1/protein-structure/alphafold2/multimer/predict-structure-from-sequences"
    MODEL_LABEL = "alphafold2_multimer"

    def __init__(self, client: NvidiaNimClient):
        self._client = client

    async def predict(self, sequences: List[str], **options: Any) -> Dict[str, Any]:
        if len(sequences) < 2:
            raise ValueError("AlphaFold2 Multimer requires 2 or more chain sequences.")
        payload = {
            "sequences": sequences,
            "algorithm": options.get("algorithm", "jackhmmer"),
            "relax_prediction": options.get("relax_prediction", False),
        }
        return await self._client.post(
            self.PATH, payload, provider_label="nvidia", model_label=self.MODEL_LABEL
        )


class NvidiaOpenFold3Provider:
    PATH = "/v1/biology/openfold/openfold3/predict"
    MODEL_LABEL = "openfold3"

    def __init__(self, client: NvidiaNimClient):
        self._client = client

    async def predict(self, sequences: List[str], **options: Any) -> Dict[str, Any]:
        # Protein-only payload, matching the conceptual schema. DNA/RNA/ligand
        # molecule types exist in the real OpenFold3 API but are deliberately
        # not exposed here (brief: "do not expose every option in the UI initially").
        molecules = [
            {"type": "protein", "id": chr(ord("A") + index), "sequence": sequence}
            for index, sequence in enumerate(sequences)
        ]
        payload = {
            "request_id": options.get("request_id", "neolysis-request"),
            "inputs": [{"input_id": "protein-1", "molecules": molecules}],
        }
        return await self._client.post(
            self.PATH, payload, provider_label="nvidia", model_label=self.MODEL_LABEL
        )


class NvidiaBoltz2Provider:
    PATH = "/v1/biology/mit/boltz2/predict"
    MODEL_LABEL = "boltz2"

    def __init__(self, client: NvidiaNimClient):
        self._client = client

    async def predict(self, sequences: List[str], **options: Any) -> Dict[str, Any]:
        ligands: Optional[List[dict]] = options.get("ligands")
        if ligands:
            # The brief explicitly requires inspecting NVIDIA's live ligand
            # schema before implementing this rather than guessing field
            # structure. That inspection requires network access to NVIDIA,
            # which is out of scope for this session.
            raise NotImplementedError(
                "Boltz-2 protein+ligand payloads are not implemented yet. NVIDIA's live "
                "ligand/affinity schema must be inspected before wiring this, rather than "
                "guessing field structure. Protein-only Boltz-2 requests are supported."
            )
        polymers = [
            {"id": chr(ord("A") + index), "molecule_type": "protein", "sequence": sequence}
            for index, sequence in enumerate(sequences)
        ]
        payload = {"polymers": polymers}
        return await self._client.post(
            self.PATH, payload, provider_label="nvidia", model_label=self.MODEL_LABEL
        )


class NvidiaColabFoldMsaProvider:
    PATH = "/v1/biology/colabfold/msa-search/predict"
    MODEL_LABEL = "colabfold_msa_search"

    def __init__(self, client: NvidiaNimClient):
        self._client = client

    async def search(self, sequence: str, databases: List[str], output_alignment_formats: List[str]) -> Dict[str, Any]:
        payload = {
            "sequence": sequence,
            "databases": databases,
            "output_alignment_formats": output_alignment_formats,
        }
        return await self._client.post(
            self.PATH, payload, provider_label="nvidia", model_label=self.MODEL_LABEL
        )


class NvidiaProteinMpnnProvider:
    PATH = "/v1/biology/ipd/proteinmpnn/predict"
    MODEL_LABEL = "proteinmpnn"

    def __init__(self, client: NvidiaNimClient):
        self._client = client

    async def design(
        self,
        input_pdb: str,
        ca_only: bool,
        use_soluble_model: bool,
        num_seq_per_target: int,
        sampling_temp: List[float],
    ) -> Dict[str, Any]:
        payload = {
            "input_pdb": input_pdb,
            "ca_only": ca_only,
            "use_soluble_model": use_soluble_model,
            "num_seq_per_target": num_seq_per_target,
            "sampling_temp": sampling_temp,
        }
        return await self._client.post(
            self.PATH, payload, provider_label="nvidia", model_label=self.MODEL_LABEL
        )
