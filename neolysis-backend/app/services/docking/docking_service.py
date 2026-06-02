import uuid
from pathlib import Path

from fastapi import HTTPException, status

from app.config import settings
from app.schemas.docking import (
    DockingGrid,
    DockingJobCreate,
    DockingJobRecord,
    DockingJobWithResult,
    DockingPoseResponse,
    DockingResultRecord,
)
from app.schemas.project_workflow import DockingJobRequest
from app.schemas.project_workflow import utc_now
from app.services.docking.docking_parser import DockingOutputParser
from app.services.docking.docking_runner import DockingRunner
from app.services.docking.interaction_analyzer import InteractionAnalyzer
from app.services.docking.kaggle_kernel import KaggleKernelJobRunner, KaggleKernelService, KaggleOutputParser
from app.services.docking.ligand_preparation import LigandPreparationService
from app.services.docking.receptor_preparation import ReceptorPreparationService
from app.services.project_workflow import project_workflow_service


class DockingService:
    def __init__(self) -> None:
        self._jobs: dict[str, DockingJobRecord] = {}
        self._results: dict[str, DockingResultRecord] = {}
        self.ligand_preparation = LigandPreparationService()
        self.receptor_preparation = ReceptorPreparationService()
        self.runner = DockingRunner()
        self.parser = DockingOutputParser()
        self.interaction_analyzer = InteractionAnalyzer()
        self.kaggle_kernel_service = KaggleKernelService()
        self.kaggle_runner = KaggleKernelJobRunner()
        self.kaggle_output_parser = KaggleOutputParser()

    def create_job(self, project_id: str, payload: DockingJobCreate) -> DockingJobRecord:
        detail = project_workflow_service.get_detail(project_id)
        structure = next((item for item in detail.structures if item.id == payload.structure_id), None)
        substrate = next((item for item in detail.substrates if item.id == payload.substrate_id), None)
        if structure is None:
            raise self._unprocessable("Structure is missing for this project.")
        if substrate is None:
            raise self._unprocessable("Substrate is missing for this project.")

        job = DockingJobRecord(
            id=self._id(),
            project_id=project_id,
            structure_id=payload.structure_id,
            substrate_id=payload.substrate_id,
            receptor_source_path=structure.storage_path or structure.uploaded_pdb_path,
            ligand_source_smiles=substrate.smiles,
            ligand_storage_path=substrate.sdf_path,
            grid_center_x=payload.grid_center.x,
            grid_center_y=payload.grid_center.y,
            grid_center_z=payload.grid_center.z,
            grid_size_x=payload.grid_size.x,
            grid_size_y=payload.grid_size.y,
            grid_size_z=payload.grid_size.z,
            engine=payload.engine,
            compute_backend=payload.compute_backend,
            exhaustiveness=payload.exhaustiveness,
            status="pending",
            created_at=utc_now(),
        )
        self._jobs[job.id] = job
        project_workflow_service.add_docking_job(
            project_id,
            DockingJobRequest(
                structure_id=job.structure_id,
                substrate_id=job.substrate_id,
                status=job.status,
                grid_center=self._grid_to_dict(payload.grid_center),
                grid_size=self._grid_to_dict(payload.grid_size),
                notes=f"Docking job {job.id} registered for fast structure-based docking hypothesis generation.",
            ),
        )
        return job

    def list_project_jobs(self, project_id: str) -> list[DockingJobWithResult]:
        project_workflow_service.get_detail(project_id)
        return [
            self.get_job(job.id)
            for job in self._jobs.values()
            if job.project_id == project_id
        ]

    def get_job(self, job_id: str) -> DockingJobWithResult:
        job = self._jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docking job not found.")
        return DockingJobWithResult(job=job, result=self._results.get(job_id))

    def run_job(self, job_id: str) -> DockingJobWithResult:
        job = self._job(job_id)
        detail = project_workflow_service.get_detail(job.project_id)
        structure = next((item for item in detail.structures if item.id == job.structure_id), None)
        substrate = next((item for item in detail.substrates if item.id == job.substrate_id), None)
        if structure is None or substrate is None:
            return self._fail(job, "Docking job references a missing structure or substrate.")
        if not structure.raw_pdb_text:
            return self._fail(job, "Docking requires raw PDB text or a stored PDB path for this MVP.")
        if job.compute_backend == "kaggle":
            return self._run_kaggle_job(job, structure.raw_pdb_text, substrate.smiles)
        if job.engine != "quickvina2":
            return self._fail(job, f"Engine '{job.engine}' is not implemented yet.")

        workdir = self._job_workdir(job)
        job.status = "preparing"
        job.started_at = utc_now()
        job.error_message = None

        receptor = self.receptor_preparation.prepare_from_pdb_text(
            structure.raw_pdb_text,
            workdir / "receptor",
            chain_id=structure.chain_id,
        )
        if not receptor.success or not receptor.receptor_pdb_path or not receptor.receptor_pdbqt_path:
            return self._fail(job, receptor.error_message or "Receptor preparation failed.")
        job.receptor_storage_path = receptor.receptor_pdbqt_path

        ligand = self.ligand_preparation.prepare_from_smiles(substrate.smiles, workdir / "ligand")
        if not ligand.success or not ligand.ligand_pdbqt_path:
            return self._fail(job, ligand.error_message or "Ligand preparation failed.")
        job.ligand_storage_path = ligand.ligand_pdbqt_path

        job.status = "running"
        run = self.runner.run_quickvina2(
            receptor.receptor_pdbqt_path,
            ligand.ligand_pdbqt_path,
            (job.grid_center_x, job.grid_center_y, job.grid_center_z),
            (job.grid_size_x, job.grid_size_y, job.grid_size_z),
            job.exhaustiveness,
            workdir,
        )
        if not run.success:
            return self._fail(job, run.error_message or "Docking runner failed.")

        raw_output = run.stdout + "\n" + run.stderr
        try:
            parsed = self.parser.parse_vina_like_output(raw_output)
        except ValueError as exc:
            return self._fail(job, str(exc))

        contacts = self.interaction_analyzer.analyze_contacts(
            receptor.receptor_pdb_path,
            run.output_pose_path,
            cutoff_angstrom=4.0,
        )
        result = DockingResultRecord(
            id=self._id(),
            docking_job_id=job.id,
            binding_affinity=parsed.binding_affinity,
            pose_rank=parsed.pose_rank,
            rmsd_lb=parsed.rmsd_lb,
            rmsd_ub=parsed.rmsd_ub,
            output_pose_path=run.output_pose_path,
            output_log_path=run.output_log_path,
            interacting_residues_json=contacts,
            raw_engine_output=raw_output,
            execution_backend="local",
            created_at=utc_now(),
        )
        self._results[job.id] = result
        job.status = "completed"
        job.completed_at = utc_now()
        return DockingJobWithResult(job=job, result=result)

    def _run_kaggle_job(self, job: DockingJobRecord, receptor_pdb_text: str, ligand_smiles: str) -> DockingJobWithResult:
        workdir = self._job_workdir(job)
        job.status = "preparing"
        job.started_at = utc_now()
        job.error_message = None
        try:
            submission = self.kaggle_kernel_service.create_kernel_folder(
                job,
                receptor_pdb_text,
                ligand_smiles,
                workdir,
            )
        except RuntimeError as exc:
            return self._fail(job, str(exc))

        job.remote_kernel_ref = submission.kernel_ref
        job.status = "running"
        run = self.kaggle_runner.run_kernel(submission)
        if not run.success:
            return self._fail(job, run.error_message or "Kaggle docking submission failed.")

        job.remote_output_path = str(run.output_dir)
        try:
            parsed = self.kaggle_output_parser.parse_output(run.output_dir)
        except ValueError as exc:
            return self._fail(job, str(exc))

        result = DockingResultRecord(
            id=self._id(),
            docking_job_id=job.id,
            binding_affinity=parsed["binding_affinity"],
            pose_rank=parsed["pose_rank"],
            rmsd_lb=parsed["rmsd_lb"],
            rmsd_ub=parsed["rmsd_ub"],
            output_pose_path=parsed["output_pose_path"],
            output_log_path=parsed["output_log_path"],
            interacting_residues_json=parsed["interacting_residues"],
            raw_engine_output=parsed["raw_engine_output"],
            execution_backend="kaggle",
            remote_kernel_ref=submission.kernel_ref,
            created_at=utc_now(),
        )
        self._results[job.id] = result
        job.status = "completed"
        job.completed_at = utc_now()
        return DockingJobWithResult(job=job, result=result)

    def get_pose(self, job_id: str) -> DockingPoseResponse:
        job_with_result = self.get_job(job_id)
        result = job_with_result.result
        if not result:
            return DockingPoseResponse(job_id=job_id)
        pose_path = Path(result.output_pose_path)
        pose_text = pose_path.read_text(encoding="utf-8") if pose_path.exists() else None
        return DockingPoseResponse(
            job_id=job_id,
            output_pose_path=result.output_pose_path,
            pose_text=pose_text,
        )

    def _fail(self, job: DockingJobRecord, message: str) -> DockingJobWithResult:
        job.status = "failed"
        job.error_message = message
        job.completed_at = utc_now()
        return DockingJobWithResult(job=job, result=self._results.get(job.id))

    def _job(self, job_id: str) -> DockingJobRecord:
        job = self._jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docking job not found.")
        return job

    @staticmethod
    def _grid_to_dict(grid: DockingGrid) -> dict[str, float]:
        return {"x": grid.x, "y": grid.y, "z": grid.z}

    @staticmethod
    def _id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _unprocessable(message: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

    @staticmethod
    def _job_workdir(job: DockingJobRecord) -> Path:
        return Path(settings.DOCKING_WORKDIR) / job.project_id / job.id


docking_service = DockingService()
