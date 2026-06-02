import pytest


SAMPLE_SEQUENCE = (
    "MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGEENFKALVLIAFAQYLQQCPFEDH"
    "VKLVNEVTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEPERNECFL"
    "SHKDDSPDLPKLKPDPNTLCDEFKADEKKFWGKYLYEIARRHPYFYAPELLYYANKYNGVFQECC"
)

SAMPLE_PDB = """\
ATOM      1  N   SER A  10      11.104  13.207  14.110  1.00 20.00           N
ATOM      2  CA  SER A  10      12.560  13.200  14.320  1.00 20.00           C
ATOM      3  N   HIS A  57      15.104  10.207  12.110  1.00 20.00           N
ATOM      4  N   ASP A 102      18.104  12.207  10.110  1.00 20.00           N
END
"""


@pytest.mark.asyncio
async def test_project_structure_aware_workflow(client):
    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Protease detergent optimization",
            "enzyme_name": "alkaline protease candidate",
            "objective": "Prioritize variants before wet-lab screening",
            "target_industry": "detergent",
        },
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["id"]

    sequence_response = await client.post(
        f"/api/v1/projects/{project_id}/sequence",
        json={"sequence": SAMPLE_SEQUENCE},
    )
    assert sequence_response.status_code == 200
    assert sequence_response.json()["is_valid"] is True

    structure_response = await client.post(
        f"/api/v1/projects/{project_id}/structure",
        json={
            "source_type": "uploaded_pdb",
            "chain_id": "A",
            "raw_pdb_text": SAMPLE_PDB,
        },
    )
    assert structure_response.status_code == 200
    structure_id = structure_response.json()["id"]

    substrate_response = await client.post(
        f"/api/v1/projects/{project_id}/substrates",
        json={"name": "model ester", "smiles": "CCOC(=O)C", "role": "substrate"},
    )
    assert substrate_response.status_code == 200
    assert substrate_response.json()["validation_notes"]

    active_site_response = await client.post(
        f"/api/v1/projects/{project_id}/active-site",
        json={
            "structure_id": structure_id,
            "name": "Catalytic triad",
            "residues": ["S10", "H57", "D102"],
            "notes": "Manual literature-derived placeholder",
        },
    )
    assert active_site_response.status_code == 200
    assert active_site_response.json()["residue_positions"] == [10, 57, 102]

    variant_response = await client.post(
        f"/api/v1/projects/{project_id}/variants/generate",
        json={"max_variants": 6},
    )
    assert variant_response.status_code == 200
    variants = variant_response.json()
    assert variants
    assert "computational prioritization" in variants[0]["explanation"]

    report_response = await client.post(f"/api/v1/projects/{project_id}/reports/generate")
    assert report_response.status_code == 200
    report = report_response.json()
    assert "Structure-Aware Enzyme Variant Prioritization Memo" in report["markdown_report"]
    assert report["report_json"]["top_variant_candidates"]
