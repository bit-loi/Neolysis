import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings
from app.schemas.docking import DockingJobRecord


@dataclass
class KaggleKernelConfig:
    username: str
    key: str
    owner_username: str
    visibility: str
    poll_interval_seconds: int
    timeout_seconds: int

    @classmethod
    def from_settings(cls) -> "KaggleKernelConfig":
        username = settings.KAGGLE_USERNAME
        key = settings.KAGGLE_KEY
        owner = settings.KAGGLE_OWNER_USERNAME or username
        missing = [
            name
            for name, value in {
                "KAGGLE_USERNAME": username,
                "KAGGLE_KEY": key,
                "KAGGLE_OWNER_USERNAME": owner,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing Kaggle credentials: "
                + ", ".join(missing)
                + ". Set Kaggle environment variables before submitting remote docking jobs."
            )
        return cls(
            username=username or "",
            key=key or "",
            owner_username=owner or "",
            visibility=settings.KAGGLE_KERNEL_VISIBILITY,
            poll_interval_seconds=settings.KAGGLE_POLL_INTERVAL_SECONDS,
            timeout_seconds=settings.KAGGLE_TIMEOUT_SECONDS,
        )


@dataclass
class KaggleKernelSubmission:
    kernel_ref: str
    kernel_dir: Path
    output_dir: Path
    slug: str


@dataclass
class KaggleRunOutput:
    success: bool
    kernel_ref: str
    kernel_dir: Path
    output_dir: Path
    stdout: str = ""
    stderr: str = ""
    error_message: str | None = None


class KaggleKernelService:
    def create_kernel_folder(
        self,
        job: DockingJobRecord,
        receptor_pdb_text: str,
        ligand_smiles: str,
        workdir: Path,
    ) -> KaggleKernelSubmission:
        kernel_dir = workdir / "kaggle_kernel"
        output_dir = workdir / "kaggle_output"
        kernel_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        config = KaggleKernelConfig.from_settings()
        slug = self._kernel_slug(job)
        kernel_ref = f"{config.owner_username}/{slug}"
        (kernel_dir / "receptor.pdb").write_text(receptor_pdb_text, encoding="utf-8")
        (kernel_dir / "input.json").write_text(
            json.dumps(
                {
                    "job_id": job.id,
                    "ligand_smiles": ligand_smiles,
                    "grid_center": {
                        "x": job.grid_center_x,
                        "y": job.grid_center_y,
                        "z": job.grid_center_z,
                    },
                    "grid_size": {
                        "x": job.grid_size_x,
                        "y": job.grid_size_y,
                        "z": job.grid_size_z,
                    },
                    "engine": job.engine,
                    "exhaustiveness": job.exhaustiveness,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (kernel_dir / "kernel-metadata.json").write_text(
            json.dumps(
                {
                    "id": kernel_ref,
                    "title": f"Neolysis docking {job.id[:8]}",
                    "code_file": "docking_worker.py",
                    "language": "python",
                    "kernel_type": "script",
                    "is_private": config.visibility != "public",
                    "enable_gpu": False,
                    "enable_internet": True,
                    "dataset_sources": [],
                    "competition_sources": [],
                    "kernel_sources": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (kernel_dir / "docking_worker.py").write_text(self._worker_script(), encoding="utf-8")
        return KaggleKernelSubmission(
            kernel_ref=kernel_ref,
            kernel_dir=kernel_dir,
            output_dir=output_dir,
            slug=slug,
        )

    @staticmethod
    def _kernel_slug(job: DockingJobRecord) -> str:
        safe = re.sub(r"[^a-z0-9-]", "-", job.id.lower())
        return f"neolysis-docking-{safe[:18]}"

    @staticmethod
    def _worker_script() -> str:
        return r'''
import json
import math
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(".")
OUT = Path("/kaggle/working")


def write_failure(message, raw_log=""):
    (OUT / "docking.log").write_text(raw_log + "\n" + message, encoding="utf-8")
    (OUT / "results.json").write_text(json.dumps({
        "success": False,
        "error_message": message,
        "binding_affinity": None,
        "pose_rank": None,
        "rmsd_lb": None,
        "rmsd_ub": None,
        "interacting_residues": {"cutoff_angstrom": 4.0, "residues": []}
    }, indent=2), encoding="utf-8")


def run(command, timeout=600):
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def find_binary(*names):
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


def parse_vina_output(text):
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            rank = int(parts[0])
            affinity = float(parts[1])
            rmsd_lb = float(parts[2]) if len(parts) > 2 else None
            rmsd_ub = float(parts[3]) if len(parts) > 3 else None
            rows.append((rank, affinity, rmsd_lb, rmsd_ub))
        except ValueError:
            continue
    if not rows:
        raise ValueError("Could not parse Vina-style docking affinity table.")
    rows.sort(key=lambda item: (item[0], item[1]))
    return rows[0]


def parse_atoms(path, protein):
    atoms = []
    for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        if protein and not line.startswith("ATOM"):
            continue
        if not protein and not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            atom = {
                "chain": line[21].strip(),
                "residue_name": line[17:20].strip(),
                "residue_number": int(line[22:26].strip()) if protein else 0,
                "x": float(line[30:38].strip()),
                "y": float(line[38:46].strip()),
                "z": float(line[46:54].strip()),
            }
            atoms.append(atom)
        except ValueError:
            continue
    return atoms


def contacts(receptor_pdb, ligand_pose, cutoff=4.0):
    protein_atoms = parse_atoms(receptor_pdb, True)
    ligand_atoms = parse_atoms(ligand_pose, False)
    found = {}
    for pa in protein_atoms:
        for la in ligand_atoms:
            dist = math.sqrt((pa["x"] - la["x"]) ** 2 + (pa["y"] - la["y"]) ** 2 + (pa["z"] - la["z"]) ** 2)
            if dist <= cutoff:
                key = (pa["chain"], pa["residue_name"], pa["residue_number"])
                label = f'{pa["chain"]}:{pa["residue_name"]}{pa["residue_number"]}' if pa["chain"] else f'{pa["residue_name"]}{pa["residue_number"]}'
                if key not in found or dist < found[key]["min_distance"]:
                    found[key] = {
                        "chain": pa["chain"],
                        "residue_name": pa["residue_name"],
                        "residue_number": pa["residue_number"],
                        "label": label,
                        "min_distance": round(dist, 3),
                    }
    return {
        "cutoff_angstrom": cutoff,
        "method": "distance_based_contacts",
        "residues": sorted(found.values(), key=lambda item: item["min_distance"]),
        "limitations": ["Distance-based contacts are docking-derived hypotheses, not confirmed interactions."]
    }


try:
    config = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
    receptor_pdb = ROOT / "receptor.pdb"
    ligand_smi = OUT / "ligand.smi"
    ligand_sdf = OUT / "ligand.sdf"
    ligand_pdbqt = OUT / "ligand.pdbqt"
    receptor_pdbqt = OUT / "receptor.pdbqt"
    pose_path = OUT / "output_pose.pdbqt"
    ligand_smi.write_text(config["ligand_smiles"] + "\n", encoding="utf-8")

    obabel = find_binary("obabel")
    if not obabel:
        write_failure("OpenBabel (`obabel`) is not available in the Kaggle runtime.")
        raise SystemExit(1)

    ligand_cmd = [obabel, "-ismi", str(ligand_smi), "-osdf", "-O", str(ligand_sdf), "--gen3d"]
    ligand_prep = run(ligand_cmd)
    if ligand_prep.returncode != 0:
        write_failure("Ligand preparation failed in Kaggle.", ligand_prep.stdout + "\n" + ligand_prep.stderr)
        raise SystemExit(1)

    ligand_pdbqt_cmd = [obabel, str(ligand_sdf), "-O", str(ligand_pdbqt)]
    ligand_convert = run(ligand_pdbqt_cmd)
    if ligand_convert.returncode != 0:
        write_failure("Ligand PDBQT conversion failed in Kaggle.", ligand_convert.stdout + "\n" + ligand_convert.stderr)
        raise SystemExit(1)

    receptor_cmd = [obabel, str(receptor_pdb), "-O", str(receptor_pdbqt), "-xr"]
    receptor_convert = run(receptor_cmd)
    if receptor_convert.returncode != 0:
        write_failure("Receptor PDBQT conversion failed in Kaggle.", receptor_convert.stdout + "\n" + receptor_convert.stderr)
        raise SystemExit(1)

    engine = config.get("engine", "quickvina2")
    if engine == "quickvina2":
        binary = find_binary("quickvina2", "qvina2")
    elif engine == "smina":
        binary = find_binary("smina")
    else:
        binary = find_binary("vina")
    if not binary:
        write_failure(f"Docking executable for engine '{engine}' is not available in the Kaggle runtime.")
        raise SystemExit(1)

    center = config["grid_center"]
    size = config["grid_size"]
    command = [
        binary,
        "--receptor", str(receptor_pdbqt),
        "--ligand", str(ligand_pdbqt),
        "--center_x", str(center["x"]),
        "--center_y", str(center["y"]),
        "--center_z", str(center["z"]),
        "--size_x", str(size["x"]),
        "--size_y", str(size["y"]),
        "--size_z", str(size["z"]),
        "--exhaustiveness", str(config.get("exhaustiveness", 4)),
        "--out", str(pose_path),
    ]
    dock = run(command, timeout=7200)
    raw = dock.stdout + "\n" + dock.stderr
    (OUT / "docking.log").write_text(raw, encoding="utf-8")
    if dock.returncode != 0:
        write_failure("Docking execution failed in Kaggle.", raw)
        raise SystemExit(1)

    rank, affinity, rmsd_lb, rmsd_ub = parse_vina_output(raw)
    contact_result = contacts(str(receptor_pdb), str(pose_path), cutoff=4.0)
    (OUT / "results.json").write_text(json.dumps({
        "success": True,
        "binding_affinity": affinity,
        "pose_rank": rank,
        "rmsd_lb": rmsd_lb,
        "rmsd_ub": rmsd_ub,
        "output_pose_path": "output_pose.pdbqt",
        "output_log_path": "docking.log",
        "interacting_residues": contact_result,
        "raw_engine_output": raw,
    }, indent=2), encoding="utf-8")
except Exception as exc:
    write_failure(f"Unhandled Kaggle docking worker error: {exc}")
    raise
'''


class KaggleKernelJobRunner:
    def run_kernel(self, submission: KaggleKernelSubmission) -> KaggleRunOutput:
        try:
            config = KaggleKernelConfig.from_settings()
        except RuntimeError as exc:
            return KaggleRunOutput(
                success=False,
                kernel_ref="",
                kernel_dir=submission.kernel_dir,
                output_dir=submission.output_dir,
                error_message=str(exc),
            )

        if not shutil.which("kaggle"):
            return KaggleRunOutput(
                success=False,
                kernel_ref=submission.kernel_ref,
                kernel_dir=submission.kernel_dir,
                output_dir=submission.output_dir,
                error_message="Kaggle CLI executable not found. Install `kaggle` and configure credentials.",
            )

        env = self._env(config)
        push = self._run(["kaggle", "kernels", "push", "-p", str(submission.kernel_dir)], env=env)
        if push.returncode != 0:
            return KaggleRunOutput(
                success=False,
                kernel_ref=submission.kernel_ref,
                kernel_dir=submission.kernel_dir,
                output_dir=submission.output_dir,
                stdout=push.stdout,
                stderr=push.stderr,
                error_message=push.stderr or push.stdout or "Kaggle kernel submission failed.",
            )

        status_error = self._poll_until_done(submission.kernel_ref, config, env)
        if status_error:
            return KaggleRunOutput(
                success=False,
                kernel_ref=submission.kernel_ref,
                kernel_dir=submission.kernel_dir,
                output_dir=submission.output_dir,
                stdout=push.stdout,
                stderr=push.stderr,
                error_message=status_error,
            )

        output = self._run(
            ["kaggle", "kernels", "output", submission.kernel_ref, "-p", str(submission.output_dir)],
            env=env,
        )
        if output.returncode != 0:
            return KaggleRunOutput(
                success=False,
                kernel_ref=submission.kernel_ref,
                kernel_dir=submission.kernel_dir,
                output_dir=submission.output_dir,
                stdout=output.stdout,
                stderr=output.stderr,
                error_message=output.stderr or output.stdout or "Kaggle output download failed.",
            )

        return KaggleRunOutput(
            success=True,
            kernel_ref=submission.kernel_ref,
            kernel_dir=submission.kernel_dir,
            output_dir=submission.output_dir,
            stdout=push.stdout + "\n" + output.stdout,
            stderr=push.stderr + "\n" + output.stderr,
        )

    def _poll_until_done(self, kernel_ref: str, config: KaggleKernelConfig, env: dict[str, str]) -> str | None:
        deadline = time.time() + config.timeout_seconds
        last_output = ""
        while time.time() < deadline:
            status_result = self._run(["kaggle", "kernels", "status", kernel_ref], env=env)
            last_output = status_result.stdout + "\n" + status_result.stderr
            normalized = last_output.lower()
            if status_result.returncode != 0:
                return last_output.strip() or "Kaggle status polling failed."
            if any(word in normalized for word in ["complete", "completed", "success"]):
                return None
            if any(word in normalized for word in ["error", "failed", "canceled", "cancelled"]):
                return last_output.strip() or "Kaggle kernel execution failed."
            time.sleep(config.poll_interval_seconds)
        return f"Kaggle kernel did not finish before timeout. Last status: {last_output.strip()}"

    @staticmethod
    def _run(command: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(command, capture_output=True, text=True, check=False, env=env)

    @staticmethod
    def _env(config: KaggleKernelConfig) -> dict[str, str]:
        env = os.environ.copy()
        env["KAGGLE_USERNAME"] = config.username
        env["KAGGLE_KEY"] = config.key
        return env


class KaggleOutputParser:
    def parse_output(self, output_dir: Path) -> dict[str, Any]:
        results_path = output_dir / "results.json"
        log_path = output_dir / "docking.log"
        pose_path = output_dir / "output_pose.pdbqt"
        if not results_path.exists():
            raise ValueError("Kaggle output is missing results.json.")
        results = json.loads(results_path.read_text(encoding="utf-8"))
        if not results.get("success"):
            raise ValueError(results.get("error_message") or "Kaggle docking worker failed.")
        if not pose_path.exists():
            raise ValueError("Kaggle output is missing output_pose.pdbqt.")
        if not log_path.exists():
            raise ValueError("Kaggle output is missing docking.log.")
        return {
            "binding_affinity": float(results["binding_affinity"]),
            "pose_rank": int(results.get("pose_rank") or 1),
            "rmsd_lb": results.get("rmsd_lb"),
            "rmsd_ub": results.get("rmsd_ub"),
            "output_pose_path": str(pose_path),
            "output_log_path": str(log_path),
            "interacting_residues": results.get("interacting_residues", {}),
            "raw_engine_output": results.get("raw_engine_output") or log_path.read_text(encoding="utf-8"),
        }
