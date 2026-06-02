# Neolysis Docking MVP

Neolysis supports fast structure-based docking for early-stage binding hypothesis generation. Docking outputs are computational hypotheses, not proof of binding, catalysis, activity, or wet-lab performance.

## Dependencies

Required for the full local pipeline:

- RDKit for SMILES validation, conformer generation, and SDF writing
- OpenBabel (`obabel`) for SDF/PDB to PDBQT conversion
- QuickVina 2 (`quickvina2` or `qvina2`) for docking

Future adapters can add Meeko, Smina, AutoDock Vina, or a separate worker image.

## Environment Variables

- `QUICKVINA_BIN`: absolute path to the QuickVina 2 executable. If unset, Neolysis searches `quickvina2` and `qvina2` on `PATH`.
- `DOCKING_WORKDIR`: storage path for docking inputs, logs, and output poses. Default: `storage/docking`.
- `DOCKING_TIMEOUT_SECONDS`: subprocess timeout. Default: `300`.

## Local Flow

1. Create a project.
2. Add a protein structure with raw PDB text.
3. Add a substrate with SMILES.
4. Create a docking job with grid center and grid size.
5. Run the job.

Example request:

```json
{
  "structure_id": "structure-id",
  "substrate_id": "substrate-id",
  "grid_center": {"x": 10.0, "y": 20.0, "z": 5.0},
  "grid_size": {"x": 20.0, "y": 20.0, "z": 20.0},
  "engine": "quickvina2",
  "compute_backend": "local",
  "exhaustiveness": 4
}
```

## API Endpoints

- `POST /api/v1/projects/{project_id}/docking/jobs`
- `GET /api/v1/projects/{project_id}/docking/jobs`
- `GET /api/v1/docking/jobs/{job_id}`
- `POST /api/v1/docking/jobs/{job_id}/run`
- `GET /api/v1/docking/jobs/{job_id}/pose`

Set `compute_backend` to `kaggle` to submit the job as a remote Kaggle batch kernel. See `docs/DockingKaggle.md`.

## Common Failure Modes

- Invalid SMILES: RDKit cannot parse the ligand.
- Conformer generation failed: RDKit could not produce a 3D ligand geometry.
- PDBQT conversion failed: OpenBabel or another converter is missing or failed.
- QuickVina binary missing: set `QUICKVINA_BIN` or install `quickvina2`/`qvina2`.
- Output parser failed: the docking engine did not emit a Vina-style affinity table.

Neolysis does not fabricate docking poses or binding scores when any dependency is missing.

## Docker Notes

The current backend Dockerfile installs Python dependencies only. To run docking in Docker, extend the image with OpenBabel and a QuickVina 2 binary, then set `QUICKVINA_BIN` inside the container.

Recommended next step: create a dedicated docking worker image with RDKit, OpenBabel or Meeko, and QuickVina 2 installed, then move `/run` execution to an async queue.
