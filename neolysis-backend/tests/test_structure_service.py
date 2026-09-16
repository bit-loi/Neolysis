"""
Unit tests for StructureService and the structure schemas. All NVIDIA calls
are mocked. NVIDIA_API_KEY is unset in this environment, so
NvidiaNotConfiguredError paths are exercised directly (no live network access
is required or attempted).
"""
import pytest

from app.schemas.structure import (
    MsaSearchRequest,
    ProteinMpnnRequest,
    StructureJobRequest,
)
from app.services.structure_service import NvidiaNotConfiguredError, StructureService


@pytest.mark.asyncio
async def test_submit_job_without_nvidia_configured_fails_with_clear_error():
    """
    NVIDIA_API_KEY is not configured in this environment. The job must fail
    with an explicit, observable error rather than hanging, silently doing
    nothing, or falling back to a different model and pretending it's equivalent.
    """
    service = StructureService()
    request = StructureJobRequest(model="openfold3", sequences=["MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKR"])

    job = service.submit_job(request)
    assert job.status == "queued"

    # Wait for the fire-and-forget asyncio task to run.
    await _wait_for_terminal_status(service, job.job_id)

    completed_job = service.get_job(job.job_id)
    assert completed_job.status == "failed"
    assert completed_job.error_code == "NvidiaNotConfiguredError"
    assert "NVIDIA_API_KEY" in completed_job.error_message


@pytest.mark.asyncio
async def test_cache_key_includes_provider_model_and_parameters_not_just_sequence_hash():
    """
    Two requests for the same sequence but different models must produce
    different cache keys, so a cached AlphaFold2 structure is never returned
    for an OpenFold3 request. submit_job() schedules a background task via
    asyncio.create_task(), which requires a running event loop — exactly like
    the real caller (an async FastAPI route handler) provides.
    """
    service = StructureService()
    sequence = "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKR"

    job_a = service.submit_job(StructureJobRequest(model="alphafold2", sequences=[sequence]))
    job_b = service.submit_job(StructureJobRequest(model="openfold3", sequences=[sequence]))

    assert job_a.cache_key != job_b.cache_key
    assert "alphafold2" in job_a.cache_key
    assert "openfold3" in job_b.cache_key

    # Let both background jobs reach a terminal state before the test exits,
    # so no unawaited-task warnings leak into other tests.
    await _wait_for_terminal_status(service, job_a.job_id)
    await _wait_for_terminal_status(service, job_b.job_id)


def test_alphafold2_multimer_requires_multiple_sequences():
    with pytest.raises(ValueError):
        from app.services.nvidia.providers import NvidiaAlphaFold2MultimerProvider

        provider = NvidiaAlphaFold2MultimerProvider(client=None)
        import asyncio

        asyncio.run(provider.predict(["MKT"]))


@pytest.mark.asyncio
async def test_boltz2_with_ligands_raises_not_implemented_instead_of_guessing_schema():
    """
    The brief explicitly requires inspecting NVIDIA's live ligand schema before
    implementing protein+ligand payloads. Guessing the field structure is not
    acceptable, so this must raise NotImplementedError rather than silently
    sending a made-up payload.
    """
    from app.services.nvidia.providers import NvidiaBoltz2Provider

    provider = NvidiaBoltz2Provider(client=None)
    with pytest.raises(NotImplementedError):
        await provider.predict(["MKT"], ligands=[{"id": "L1", "smiles": "CCO"}])


@pytest.mark.asyncio
async def test_msa_search_fails_clearly_when_nvidia_not_configured():
    service = StructureService()
    with pytest.raises(NvidiaNotConfiguredError):
        await service.search_msa(MsaSearchRequest(sequence="MKTAYIAKQRQ"))


@pytest.mark.asyncio
async def test_proteinmpnn_fails_clearly_when_nvidia_not_configured():
    service = StructureService()
    with pytest.raises(NvidiaNotConfiguredError):
        await service.design_with_proteinmpnn(ProteinMpnnRequest(input_pdb="ATOM ..."))


def test_proteinmpnn_result_never_labels_output_as_ddg():
    """
    ProteinMPNN is not a \u0394\u0394G model. Its result schema must not expose
    a ddg/predicted_ddg field, and its limitations must say so explicitly.
    """
    from app.schemas.structure import ProteinMpnnDesign, ProteinMpnnResult

    design = ProteinMpnnDesign(sequence="MKT", backbone_sequence_compatibility=0.8)
    assert not hasattr(design, "ddg")
    assert not hasattr(design, "predicted_ddg")

    result = ProteinMpnnResult(designs=[design], cache_key="proteinmpnn:test", cache_hit=False)
    assert any("not a" in limitation and "ddg" in limitation.lower() for limitation in result.limitations)


async def _wait_for_terminal_status(service: StructureService, job_id: str, timeout: float = 2.0) -> None:
    import asyncio
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = service.get_job(job_id)
        if job.status in {"completed", "failed"}:
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"Job {job_id} did not reach a terminal status within {timeout}s")
