# Kaggle Docking Backend

Neolysis can submit molecular docking jobs to Kaggle as remote batch kernels. This is not an interactive notebook session. The backend generates a temporary kernel folder, pushes it with the Kaggle CLI, polls status, downloads outputs, and parses `results.json`.

## What Runs Remotely

For each docking job with `compute_backend: "kaggle"`, Neolysis creates:

- `kernel-metadata.json`
- `docking_worker.py`
- `input.json`
- `receptor.pdb`

The Kaggle worker prepares ligand and receptor files, runs the selected docking executable if present, and writes:

- `results.json`
- `docking.log`
- `output_pose.pdbqt`

The backend then downloads these files using `kaggle kernels output`.

## Environment Variables

Set these on the backend, not inside the Kaggle notebook:

- `KAGGLE_USERNAME`
- `KAGGLE_KEY`
- `KAGGLE_OWNER_USERNAME`
- `KAGGLE_KERNEL_VISIBILITY=private`
- `DOCKING_WORKDIR`

Optional:

- `KAGGLE_POLL_INTERVAL_SECONDS`
- `KAGGLE_TIMEOUT_SECONDS`

## Security

Do not put Supabase service role keys, database passwords, or private backend secrets into the Kaggle kernel.

The MVP sends only the input PDB text and ligand SMILES inside the generated kernel folder. For larger/private files, prefer signed URLs or short-lived object-storage links. Kaggle writes outputs locally, and the backend downloads outputs after execution.

## API Example

Create a job:

```json
{
  "structure_id": "structure-id",
  "substrate_id": "substrate-id",
  "grid_center": {"x": 10.0, "y": 20.0, "z": 5.0},
  "grid_size": {"x": 20.0, "y": 20.0, "z": 20.0},
  "engine": "quickvina2",
  "compute_backend": "kaggle",
  "exhaustiveness": 4
}
```

Run it:

```bash
curl -X POST http://localhost:8000/api/v1/docking/jobs/{job_id}/run
```

## Failure Handling

The backend marks the job as `failed` and stores `error_message` when:

- Kaggle credentials are missing.
- Kaggle CLI is missing.
- Kernel push fails.
- Kernel status becomes failed/error/canceled.
- Kernel output download fails.
- `results.json`, `docking.log`, or `output_pose.pdbqt` is missing.
- The Kaggle worker reports dependency or execution failure.

Neolysis does not fake binding affinity or docking poses.

## Kaggle Runtime Requirements

The generated worker expects these tools to be available in the Kaggle runtime:

- OpenBabel (`obabel`)
- `quickvina2` or `qvina2` for `engine: "quickvina2"`
- `smina` for `engine: "smina"`
- `vina` for `engine: "vina"`

If the runtime lacks the selected tools, the worker writes a failed `results.json` and `docking.log`, and the backend marks the job as failed.

## Current Limitations

- This MVP uses Kaggle CLI from the backend process and runs synchronously while polling.
- Large input files should move to signed URLs/object storage instead of embedding files in the kernel folder.
- A production version should move polling to Celery/Redis or another async queue.
- Kaggle availability and package/tool availability are external runtime constraints.
