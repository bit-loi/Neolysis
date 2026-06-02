from pathlib import Path

import pytest

from app.services.docking.docking_parser import DockingOutputParser
from app.services.docking.docking_runner import DockingRunner
from app.services.docking.kaggle_kernel import KaggleKernelConfig, KaggleOutputParser
from app.services.docking.interaction_analyzer import InteractionAnalyzer
from app.services.docking.ligand_preparation import LigandPreparationService


SAMPLE_SEQUENCE = (
    "MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGEENFKALVLIAFAQYLQQCPFEDH"
    "VKLVNEVTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEPERNECFL"
)

SAMPLE_PDB = """\
ATOM      1  N   SER A  10      11.104  13.207  14.110  1.00 20.00           N
ATOM      2  CA  SER A  10      12.560  13.200  14.320  1.00 20.00           C
ATOM      3  C   SER A  10      13.083  11.820  14.725  1.00 20.00           C
END
"""


def test_vina_output_parser_extracts_best_affinity():
    output = """
-----+------------+----------+----------
   1       -7.2      0.000      0.000
   2       -6.4      1.200      2.300
"""
    parsed = DockingOutputParser().parse_vina_like_output(output)
    assert parsed.binding_affinity == -7.2
    assert parsed.pose_rank == 1
    assert parsed.rmsd_lb == 0.0
    assert parsed.rmsd_ub == 0.0


def test_interaction_analyzer_reports_distance_based_contacts(tmp_path: Path):
    receptor = tmp_path / "receptor.pdb"
    ligand = tmp_path / "pose.pdbqt"
    receptor.write_text(SAMPLE_PDB, encoding="utf-8")
    ligand.write_text(
        "HETATM    1  C   LIG X   1      12.000  13.000  14.000  1.00  0.00           C\n",
        encoding="utf-8",
    )
    contacts = InteractionAnalyzer().analyze_contacts(str(receptor), str(ligand), cutoff_angstrom=4.0)
    assert contacts["method"] == "distance_based_contacts"
    assert contacts["residues"][0]["label"] == "A:SER10"


def test_ligand_preparation_rejects_invalid_smiles(tmp_path: Path):
    result = LigandPreparationService().prepare_from_smiles("not a smiles", tmp_path)
    assert result.success is False
    assert "Invalid SMILES" in result.error_message


def test_quickvina_runner_missing_binary_is_explicit(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("app.services.docking.docking_runner.settings.QUICKVINA_BIN", None)
    monkeypatch.setattr("app.services.docking.docking_runner.shutil.which", lambda _: None)
    result = DockingRunner().run_quickvina2(
        "receptor.pdbqt",
        "ligand.pdbqt",
        (1.0, 2.0, 3.0),
        (20.0, 20.0, 20.0),
        4,
        tmp_path,
    )
    assert result.success is False
    assert "QuickVina 2 executable not found" in result.error_message


def test_kaggle_config_missing_credentials_is_explicit(monkeypatch):
    monkeypatch.setattr("app.services.docking.kaggle_kernel.settings.KAGGLE_USERNAME", None)
    monkeypatch.setattr("app.services.docking.kaggle_kernel.settings.KAGGLE_KEY", None)
    monkeypatch.setattr("app.services.docking.kaggle_kernel.settings.KAGGLE_OWNER_USERNAME", None)
    with pytest.raises(RuntimeError, match="Missing Kaggle credentials"):
        KaggleKernelConfig.from_settings()


def test_kaggle_output_parser_reads_results(tmp_path: Path):
    (tmp_path / "results.json").write_text(
        """
{
  "success": true,
  "binding_affinity": -7.5,
  "pose_rank": 1,
  "rmsd_lb": 0.0,
  "rmsd_ub": 0.0,
  "interacting_residues": {"cutoff_angstrom": 4.0, "residues": []},
  "raw_engine_output": "1 -7.5 0.0 0.0"
}
""",
        encoding="utf-8",
    )
    (tmp_path / "docking.log").write_text("1 -7.5 0.0 0.0", encoding="utf-8")
    (tmp_path / "output_pose.pdbqt").write_text("MODEL 1\nENDMDL\n", encoding="utf-8")
    parsed = KaggleOutputParser().parse_output(tmp_path)
    assert parsed["binding_affinity"] == -7.5
    assert parsed["output_pose_path"].endswith("output_pose.pdbqt")


@pytest.mark.asyncio
async def test_docking_job_api_validation_and_failure(client):
    project_response = await client.post(
        "/api/v1/projects",
        json={"name": "Docking MVP", "enzyme_target": "test enzyme"},
    )
    project_id = project_response.json()["id"]
    structure_response = await client.post(
        f"/api/v1/projects/{project_id}/structure",
        json={"source_type": "uploaded_pdb", "chain_id": "A", "raw_pdb_text": SAMPLE_PDB},
    )
    substrate_response = await client.post(
        f"/api/v1/projects/{project_id}/substrates",
        json={"name": "ethanol", "smiles": "CCO", "role": "substrate"},
    )

    bad_job = await client.post(
        f"/api/v1/projects/{project_id}/docking/jobs",
        json={
            "structure_id": structure_response.json()["id"],
            "substrate_id": substrate_response.json()["id"],
            "grid_center": {"x": 0, "y": 0, "z": 0},
            "grid_size": {"x": 0, "y": 20, "z": 20},
            "engine": "quickvina2",
            "exhaustiveness": 4,
        },
    )
    assert bad_job.status_code == 422

    job_response = await client.post(
        f"/api/v1/projects/{project_id}/docking/jobs",
        json={
            "structure_id": structure_response.json()["id"],
            "substrate_id": substrate_response.json()["id"],
            "grid_center": {"x": 12, "y": 13, "z": 14},
            "grid_size": {"x": 20, "y": 20, "z": 20},
            "engine": "quickvina2",
            "exhaustiveness": 4,
        },
    )
    assert job_response.status_code == 200
    job_id = job_response.json()["job"]["id"]

    run_response = await client.post(f"/api/v1/docking/jobs/{job_id}/run")
    assert run_response.status_code == 200
    assert run_response.json()["job"]["status"] in {"failed", "completed"}
    if run_response.json()["job"]["status"] == "failed":
        assert run_response.json()["job"]["error_message"]


@pytest.mark.asyncio
async def test_kaggle_docking_job_fails_without_credentials(client, monkeypatch):
    monkeypatch.setattr("app.services.docking.kaggle_kernel.settings.KAGGLE_USERNAME", None)
    monkeypatch.setattr("app.services.docking.kaggle_kernel.settings.KAGGLE_KEY", None)
    monkeypatch.setattr("app.services.docking.kaggle_kernel.settings.KAGGLE_OWNER_USERNAME", None)

    project_response = await client.post(
        "/api/v1/projects",
        json={"name": "Kaggle Docking MVP", "enzyme_target": "test enzyme"},
    )
    project_id = project_response.json()["id"]
    structure_response = await client.post(
        f"/api/v1/projects/{project_id}/structure",
        json={"source_type": "uploaded_pdb", "chain_id": "A", "raw_pdb_text": SAMPLE_PDB},
    )
    substrate_response = await client.post(
        f"/api/v1/projects/{project_id}/substrates",
        json={"name": "ethanol", "smiles": "CCO", "role": "substrate"},
    )
    job_response = await client.post(
        f"/api/v1/projects/{project_id}/docking/jobs",
        json={
            "structure_id": structure_response.json()["id"],
            "substrate_id": substrate_response.json()["id"],
            "grid_center": {"x": 12, "y": 13, "z": 14},
            "grid_size": {"x": 20, "y": 20, "z": 20},
            "engine": "quickvina2",
            "compute_backend": "kaggle",
            "exhaustiveness": 4,
        },
    )
    assert job_response.status_code == 200
    job_id = job_response.json()["job"]["id"]
    run_response = await client.post(f"/api/v1/docking/jobs/{job_id}/run")
    assert run_response.status_code == 200
    body = run_response.json()
    assert body["job"]["status"] == "failed"
    assert "Missing Kaggle credentials" in body["job"]["error_message"]
