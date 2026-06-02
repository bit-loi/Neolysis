import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import settings


@dataclass
class DockingRunResult:
    success: bool
    command: list[str]
    stdout: str
    stderr: str
    output_pose_path: str
    output_log_path: str
    error_message: str | None = None


class DockingRunner:
    def run_quickvina2(
        self,
        receptor_pdbqt_path: str,
        ligand_pdbqt_path: str,
        grid_center: tuple[float, float, float],
        grid_size: tuple[float, float, float],
        exhaustiveness: int,
        workdir: Path,
    ) -> DockingRunResult:
        binary = self._resolve_quickvina_binary()
        output_pose_path = str(workdir / "docked_pose.pdbqt")
        output_log_path = str(workdir / "quickvina.log")

        if not binary:
            message = "QuickVina 2 executable not found. Set QUICKVINA_BIN or install the binary."
            Path(output_log_path).write_text(message, encoding="utf-8")
            return DockingRunResult(
                success=False,
                command=[],
                stdout="",
                stderr=message,
                output_pose_path=output_pose_path,
                output_log_path=output_log_path,
                error_message=message,
            )

        command = [
            binary,
            "--receptor",
            receptor_pdbqt_path,
            "--ligand",
            ligand_pdbqt_path,
            "--center_x",
            str(grid_center[0]),
            "--center_y",
            str(grid_center[1]),
            "--center_z",
            str(grid_center[2]),
            "--size_x",
            str(grid_size[0]),
            "--size_y",
            str(grid_size[1]),
            "--size_z",
            str(grid_size[2]),
            "--exhaustiveness",
            str(exhaustiveness),
            "--out",
            output_pose_path,
        ]

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=settings.DOCKING_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or "QuickVina 2 run timed out."
            Path(output_log_path).write_text(stdout + "\n" + stderr, encoding="utf-8")
            return DockingRunResult(
                success=False,
                command=command,
                stdout=stdout,
                stderr=stderr,
                output_pose_path=output_pose_path,
                output_log_path=output_log_path,
                error_message="QuickVina 2 run timed out.",
            )

        raw_output = completed.stdout + "\n" + completed.stderr
        Path(output_log_path).write_text(raw_output, encoding="utf-8")
        if completed.returncode != 0:
            return DockingRunResult(
                success=False,
                command=command,
                stdout=completed.stdout,
                stderr=completed.stderr,
                output_pose_path=output_pose_path,
                output_log_path=output_log_path,
                error_message=completed.stderr or completed.stdout or "QuickVina 2 returned a non-zero exit code.",
            )

        return DockingRunResult(
            success=True,
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            output_pose_path=output_pose_path,
            output_log_path=output_log_path,
        )

    @staticmethod
    def _resolve_quickvina_binary() -> str | None:
        if settings.QUICKVINA_BIN:
            return settings.QUICKVINA_BIN if os.path.exists(settings.QUICKVINA_BIN) else None
        return shutil.which("quickvina2") or shutil.which("qvina2")
