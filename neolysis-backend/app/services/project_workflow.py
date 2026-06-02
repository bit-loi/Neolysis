import re
import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from fastapi import HTTPException, status

from app.schemas.property import TargetConditions
from app.schemas.project_workflow import (
    ActiveSiteRecord,
    ActiveSiteRequest,
    AnalysisReportRecord,
    DockingJobRecord,
    DockingJobRequest,
    EnzymeSequenceRecord,
    EnzymeSequenceRequest,
    EnzymeStructureRecord,
    EnzymeStructureRequest,
    EnzymeVariantRecord,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectRecord,
    SubstrateRecord,
    SubstrateRequest,
    VariantGenerateRequest,
    utc_now,
)
from app.services.mutation_risk import mutation_risk_service
from app.services.property_scoring import property_scoring_service
from app.services.protein_features import protein_feature_service
from app.services.sequence_validation import sequence_validation_service


RESIDUE_PATTERN = re.compile(r"^([ACDEFGHIKLMNPQRSTVWY])?(\d+)([A-Za-z]?)$")
MUTATION_OPTIONS = {
    "A": ["V", "S"],
    "C": ["S", "A"],
    "D": ["E", "N"],
    "E": ["D", "Q"],
    "F": ["Y", "L"],
    "G": ["A", "S"],
    "H": ["N", "Q"],
    "I": ["V", "L"],
    "K": ["R", "Q"],
    "L": ["I", "V"],
    "M": ["L", "I"],
    "N": ["Q", "D"],
    "P": ["A", "S"],
    "Q": ["N", "E"],
    "R": ["K", "Q"],
    "S": ["T", "A"],
    "T": ["S", "V"],
    "V": ["I", "A"],
    "W": ["F", "Y"],
    "Y": ["F", "S"],
}
CATALYTIC_RESIDUES = {"S", "H", "D", "E", "C", "K", "R"}


@dataclass
class ProjectState:
    project: ProjectRecord
    sequence: EnzymeSequenceRecord | None = None
    structures: Dict[str, EnzymeStructureRecord] = field(default_factory=dict)
    substrates: Dict[str, SubstrateRecord] = field(default_factory=dict)
    active_sites: Dict[str, ActiveSiteRecord] = field(default_factory=dict)
    variants: Dict[str, EnzymeVariantRecord] = field(default_factory=dict)
    docking_jobs: Dict[str, DockingJobRecord] = field(default_factory=dict)
    reports: Dict[str, AnalysisReportRecord] = field(default_factory=dict)


class ProjectWorkflowService:
    def __init__(self):
        self._projects: Dict[str, ProjectState] = {}

    def create_project(self, payload: ProjectCreateRequest) -> ProjectRecord:
        now = utc_now()
        project = ProjectRecord(
            id=self._id(),
            created_at=now,
            updated_at=now,
            **payload.model_dump(),
        )
        self._projects[project.id] = ProjectState(project=project)
        return project

    def list_projects(self) -> List[ProjectRecord]:
        return sorted(
            (state.project for state in self._projects.values()),
            key=lambda item: item.created_at,
            reverse=True,
        )

    def get_detail(self, project_id: str) -> ProjectDetailResponse:
        state = self._state(project_id)
        return ProjectDetailResponse(
            project=state.project,
            sequence=state.sequence,
            structures=list(state.structures.values()),
            substrates=list(state.substrates.values()),
            active_sites=list(state.active_sites.values()),
            variants=self._ranked_variants(state),
            docking_jobs=list(state.docking_jobs.values()),
            reports=list(state.reports.values()),
        )

    def set_sequence(self, project_id: str, payload: EnzymeSequenceRequest) -> EnzymeSequenceRecord:
        state = self._state(project_id)
        validation = sequence_validation_service.validate(payload.sequence, name=payload.name)
        features = protein_feature_service.extract(validation.cleaned_sequence) if validation.valid else None
        record = EnzymeSequenceRecord(
            id=self._id(),
            project_id=project_id,
            sequence=validation.cleaned_sequence,
            sequence_length=validation.sequence_length,
            length=validation.sequence_length,
            molecular_weight=features.molecular_weight if features else None,
            pI=features.isoelectric_point if features else None,
            instability_index=features.instability_index if features else None,
            GRAVY=features.gravy if features else None,
            aromaticity=features.aromaticity if features else None,
            is_valid=validation.valid,
            validation_errors=validation.invalid_residues,
            validation=validation,
            feature_json=features,
            created_at=utc_now(),
        )
        state.sequence = record
        state.project.updated_at = utc_now()
        return record

    def set_structure(self, project_id: str, payload: EnzymeStructureRequest) -> EnzymeStructureRecord:
        state = self._state(project_id)
        notes: list[str] = []
        raw_pdb_text = payload.raw_pdb_text
        if payload.source_type == "uploaded_pdb" and not raw_pdb_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="uploaded_pdb requires raw_pdb_text for this MVP.",
            )
        if payload.source_type in {"pdb_id", "alphafold_db"}:
            notes.append(
                "External structure fetching is a clean API placeholder in this MVP; paste PDB text for immediate visualization."
            )
        if payload.source_type == "predicted_placeholder":
            notes.append("Predicted structures are not generated by Neolysis yet.")
        record = EnzymeStructureRecord(
            id=self._id(),
            project_id=project_id,
            confidence_notes=notes,
            raw_pdb_text=raw_pdb_text,
            source=payload.source or self._structure_source_label(payload.source_type),
            **payload.model_dump(exclude={"raw_pdb_text", "source"}),
            created_at=utc_now(),
        )
        state.structures[record.id] = record
        state.project.updated_at = utc_now()
        return record

    def add_substrate(self, project_id: str, payload: SubstrateRequest) -> SubstrateRecord:
        state = self._state(project_id)
        notes = self._validate_smiles_lightweight(payload.smiles)
        record = SubstrateRecord(
            id=self._id(),
            project_id=project_id,
            validation_notes=notes,
            created_at=utc_now(),
            **payload.model_dump(),
        )
        state.substrates[record.id] = record
        state.project.updated_at = utc_now()
        return record

    def add_active_site(self, project_id: str, payload: ActiveSiteRequest) -> ActiveSiteRecord:
        state = self._state(project_id)
        if payload.structure_id not in state.structures:
            raise self._not_found("Structure")
        residues, positions, warnings = self._parse_residue_list(payload.residues)
        structure = state.structures[payload.structure_id]
        nearby, candidates, protected = self._active_site_context(structure.raw_pdb_text or "", positions)
        record = ActiveSiteRecord(
            id=self._id(),
            project_id=project_id,
            structure_id=payload.structure_id,
            name=payload.name,
            residue_list=residues,
            residue_positions=positions,
            nearby_residues=nearby,
            mutation_candidate_residues=candidates,
            protected_residues=protected or residues,
            selection_method=payload.selection_method,
            notes=payload.notes,
            warnings=warnings,
            created_at=utc_now(),
        )
        state.active_sites[record.id] = record
        state.project.updated_at = utc_now()
        return record

    def add_docking_job(self, project_id: str, payload: DockingJobRequest) -> DockingJobRecord:
        state = self._state(project_id)
        if payload.structure_id and payload.structure_id not in state.structures:
            raise self._not_found("Structure")
        if payload.substrate_id and payload.substrate_id not in state.substrates:
            raise self._not_found("Substrate")
        record = DockingJobRecord(
            id=self._id(),
            project_id=project_id,
            created_at=utc_now(),
            **payload.model_dump(),
        )
        state.docking_jobs[record.id] = record
        state.project.updated_at = utc_now()
        return record

    def generate_variants(self, project_id: str, payload: VariantGenerateRequest) -> List[EnzymeVariantRecord]:
        state = self._state(project_id)
        if not state.sequence or not state.sequence.is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Generate variants after adding a valid enzyme sequence.",
            )

        sequence = state.sequence.sequence
        target_positions = self._variant_target_positions(state, payload)
        active_positions = self._active_site_positions(state)
        variants: list[EnzymeVariantRecord] = []
        for position in target_positions:
            if len(variants) >= payload.max_variants:
                break
            wild_type = sequence[position - 1]
            if position in active_positions and not payload.allow_catalytic_mutations:
                continue
            if wild_type in CATALYTIC_RESIDUES and position in active_positions and not payload.allow_catalytic_mutations:
                continue
            for mutant in MUTATION_OPTIONS.get(wild_type, ["A", "S"]):
                if mutant == wild_type or len(variants) >= payload.max_variants:
                    continue
                variants.append(self._score_variant(project_id, sequence, wild_type, position, mutant, active_positions))

        state.variants = {variant.id: variant for variant in variants}
        state.project.updated_at = utc_now()
        return self._ranked_variants(state)

    def generate_report(self, project_id: str) -> AnalysisReportRecord:
        state = self._state(project_id)
        variants = self._ranked_variants(state)
        top = variants[:5]
        summary = (
            f"{state.project.name} has "
            f"{state.sequence.sequence_length if state.sequence else 0} residues analyzed, "
            f"{len(state.structures)} structure record(s), {len(state.substrates)} substrate record(s), "
            f"and {len(variants)} prioritized variant candidate(s)."
        )
        report_json = {
            "executive_summary": summary,
            "input_quality_check": state.sequence.model_dump() if state.sequence else None,
            "baseline_enzyme_sequence_profile": state.sequence.feature_json.model_dump() if state.sequence and state.sequence.feature_json else None,
            "structure_context": [item.model_dump() for item in state.structures.values()],
            "active_site_context": [item.model_dump() for item in state.active_sites.values()],
            "substrate_context": [item.model_dump() for item in state.substrates.values()],
            "docking_context": [item.model_dump() for item in state.docking_jobs.values()],
            "top_variant_candidates": [item.model_dump() for item in top],
            "risk_assessment": self._risk_assessment(top),
            "wet_lab_validation_plan": self._wet_lab_plan(),
            "limitations": self._limitations(),
        }
        markdown = self._report_markdown(report_json)
        record = AnalysisReportRecord(
            id=self._id(),
            project_id=project_id,
            report_type="structure_aware_variant_prioritization_mvp",
            summary=summary,
            top_variants=[item.model_dump() for item in top],
            wet_lab_plan=report_json["wet_lab_validation_plan"],
            limitations=report_json["limitations"],
            markdown_report=markdown,
            report_json=report_json,
            created_at=utc_now(),
        )
        state.reports[record.id] = record
        return record

    def _score_variant(
        self,
        project_id: str,
        sequence: str,
        wild_type: str,
        position: int,
        mutant: str,
        active_positions: set[int],
    ) -> EnzymeVariantRecord:
        mutation = f"{wild_type}{position}{mutant}"
        mutated = sequence[: position - 1] + mutant + sequence[position:]
        property_score = property_scoring_service.score(mutated, TargetConditions()).industrial_fit_score
        risk = mutation_risk_service.analyze(
            wild_type=sequence,
            variant_sequence=mutated,
            mutations=[mutation],
            active_site_positions=sorted(active_positions),
        )
        distance_proxy = self._distance_proxy(position, active_positions)
        active_relevance = 0.35 if distance_proxy is None else (1.0 if distance_proxy == 0 else max(0.0, 1.0 - distance_proxy / 12.0))
        stability_proxy = self._stability_proxy(wild_type, mutant)
        binding_proxy = self._binding_proxy(wild_type, mutant, active_relevance)
        docking_score_normalized = binding_proxy
        final_score = (
            0.30 * property_score
            + 0.25 * active_relevance
            + 0.20 * docking_score_normalized
            + 0.15 * stability_proxy
            + 0.10 * (1 - risk.risk_score)
        )
        warnings = risk.potential_stability_risk + risk.potential_function_risk
        if position in active_positions:
            warnings.append("Defined active-site residue; do not mutate without literature or assay support.")
        explanation = (
            f"{mutation} is prioritized as a hypothesis for wet-lab screening. "
            f"Active-site relevance={active_relevance:.2f}, sequence property score={property_score:.2f}, "
            f"docking-aware proxy={docking_score_normalized:.2f}, stability proxy={stability_proxy:.2f}, "
            f"and mutation risk={risk.risk_score:.2f}. "
            "This is a computational prioritization result, not experimental proof."
        )
        return EnzymeVariantRecord(
            id=self._id(),
            project_id=project_id,
            mutation_label=mutation,
            wild_type_residue=wild_type,
            position=position,
            mutant_residue=mutant,
            reason="Structure-aware MVP heuristic around defined active-site or sequence-level candidate positions.",
            active_site_distance_proxy=distance_proxy,
            sequence_property_score=round(property_score, 3),
            active_site_relevance_score=round(active_relevance, 3),
            stability_proxy_score=round(stability_proxy, 3),
            binding_proxy_score=round(binding_proxy, 3),
            docking_score_normalized=round(docking_score_normalized, 3),
            mutation_risk_score=risk.risk_score,
            final_score=round(max(0.0, min(1.0, final_score)), 3),
            explanation=explanation,
            warnings=list(dict.fromkeys(warnings)),
            created_at=utc_now(),
        )

    def _variant_target_positions(self, state: ProjectState, payload: VariantGenerateRequest) -> list[int]:
        positions = self._parse_residue_list(payload.target_residues)[1] if payload.target_residues else []
        if not positions:
            active = sorted(self._active_site_positions(state))
            neighbors = []
            for pos in active:
                neighbors.extend([pos - 2, pos - 1, pos + 1, pos + 2])
            positions = active + neighbors
        if not positions and state.sequence:
            sequence = state.sequence.sequence
            positions = [idx + 1 for idx, aa in enumerate(sequence) if aa in {"G", "P", "S", "T", "A"}][: payload.max_variants * 2]
        max_len = state.sequence.sequence_length if state.sequence else 0
        return [pos for pos in dict.fromkeys(positions) if 1 <= pos <= max_len]

    def _active_site_positions(self, state: ProjectState) -> set[int]:
        positions: set[int] = set()
        for active_site in state.active_sites.values():
            positions.update(active_site.residue_positions)
        return positions

    def _ranked_variants(self, state: ProjectState) -> list[EnzymeVariantRecord]:
        return sorted(
            state.variants.values(),
            key=lambda item: item.final_score or 0,
            reverse=True,
        )

    def _parse_residue_list(self, residues: list[str]) -> tuple[list[str], list[int], list[str]]:
        normalized: list[str] = []
        positions: list[int] = []
        warnings: list[str] = []
        for residue in residues:
            item = residue.strip().upper()
            match = RESIDUE_PATTERN.match(item)
            if not match:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid residue format '{residue}'. Use formats like S123, H456, or 123.",
                )
            residue_letter, pos_text, chain = match.groups()
            label = f"{residue_letter or ''}{pos_text}{chain or ''}"
            normalized.append(label)
            positions.append(int(pos_text))
            if not residue_letter:
                warnings.append(f"{label} has no residue identity; position-only scoring is lower confidence.")
        return normalized, positions, warnings

    def _active_site_context(self, pdb_text: str, active_positions: list[int]) -> tuple[list[str], list[str], list[str]]:
        residue_atoms = self._parse_pdb_residue_atoms(pdb_text)
        if not residue_atoms or not active_positions:
            return [], [], []

        active_centers = [
            self._centroid(residue_atoms[position])
            for position in active_positions
            if position in residue_atoms
        ]
        if not active_centers:
            return [], [], []

        nearby: list[str] = []
        candidates: list[str] = []
        protected: list[str] = []
        active_set = set(active_positions)
        for position, atoms in sorted(residue_atoms.items()):
            label = self._residue_label_from_atoms(position, atoms)
            distance = min(self._euclidean(self._centroid(atoms), center) for center in active_centers)
            if position in active_set:
                protected.append(label)
            elif distance <= 8.0:
                nearby.append(f"{label} ({distance:.1f} A)")
                if distance >= 4.0 and atoms[0]["residue"] not in {"GLY", "PRO", "CYS"}:
                    candidates.append(label)
        return nearby, candidates, protected

    @staticmethod
    def _parse_pdb_residue_atoms(pdb_text: str) -> dict[int, list[dict]]:
        residues: dict[int, list[dict]] = {}
        for line in pdb_text.splitlines():
            if not line.startswith(("ATOM", "HETATM")):
                continue
            try:
                residue = line[17:20].strip()
                chain = line[21].strip()
                position = int(line[22:26].strip())
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
            except ValueError:
                continue
            residues.setdefault(position, []).append(
                {"residue": residue, "chain": chain, "x": x, "y": y, "z": z}
            )
        return residues

    @staticmethod
    def _centroid(atoms: list[dict]) -> tuple[float, float, float]:
        count = len(atoms)
        return (
            sum(atom["x"] for atom in atoms) / count,
            sum(atom["y"] for atom in atoms) / count,
            sum(atom["z"] for atom in atoms) / count,
        )

    @staticmethod
    def _euclidean(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5

    @staticmethod
    def _residue_label_from_atoms(position: int, atoms: list[dict]) -> str:
        atom = atoms[0]
        chain = atom["chain"]
        residue = atom["residue"]
        return f"{residue}{position}{chain}" if chain else f"{residue}{position}"

    @staticmethod
    def _distance_proxy(position: int, active_positions: set[int]) -> float | None:
        if not active_positions:
            return None
        return float(min(abs(position - active) for active in active_positions))

    @staticmethod
    def _stability_proxy(wild_type: str, mutant: str) -> float:
        if wild_type == "G" and mutant == "P":
            return 0.35
        if mutant == "P":
            return 0.66
        if wild_type in {"D", "E", "K", "R"} and mutant in {"D", "E", "K", "R"}:
            return 0.72
        if mutant in {"A", "V", "I", "L", "S", "T"}:
            return 0.68
        return 0.55

    @staticmethod
    def _binding_proxy(wild_type: str, mutant: str, active_relevance: float) -> float:
        chemical_shift = 0.58
        if mutant in {"F", "Y", "W", "V", "I", "L"}:
            chemical_shift = 0.66
        if wild_type in {"S", "T", "N", "Q"} and mutant in {"A", "V", "L"}:
            chemical_shift = 0.60
        return max(0.0, min(1.0, 0.45 + 0.35 * active_relevance + 0.20 * chemical_shift))

    @staticmethod
    def _validate_smiles_lightweight(smiles: str) -> list[str]:
        notes = ["Lightweight SMILES validation only; RDKit-backed validation can be wired later."]
        if any(char.isspace() for char in smiles):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="SMILES must not contain whitespace.",
            )
        if not re.search(r"[A-Za-z0-9]", smiles):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="SMILES does not look chemically meaningful.",
            )
        return notes

    @staticmethod
    def _structure_source_label(source_type: str) -> str:
        mapping = {
            "uploaded_pdb": "uploaded",
            "pdb_id": "pdb_id",
            "alphafold_db": "alphafold_db",
            "predicted_placeholder": "predicted",
        }
        return mapping.get(source_type, source_type)

    @staticmethod
    def _report_markdown(report: dict) -> str:
        lines = [
            "# Structure-Aware Enzyme Variant Prioritization Memo",
            "",
            "## 1. Executive Summary",
            report["executive_summary"],
            "",
            "## 2. Enzyme Baseline Profile",
            "Sequence-derived properties are included when available.",
            "",
            "## 3. Structural Context",
            f"{len(report['structure_context'])} structure record(s) available.",
            "",
            "## 4. Active-Site Analysis",
            f"{len(report['active_site_context'])} active-site definition(s) available.",
            "",
            "## 5. Variant Ranking",
        ]
        if report["top_variant_candidates"]:
            for variant in report["top_variant_candidates"]:
                lines.append(
                    f"- {variant['mutation_label']}: final score {variant['final_score']}; {variant['explanation']}"
                )
        else:
            lines.append("- No variants have been generated yet.")
        lines.extend(
            [
                "",
                "## 6. Risk Assessment",
                report["risk_assessment"],
                "",
                "## 7. Recommended Wet-Lab Validation Plan",
            ]
        )
        lines.extend(f"- {item}" for item in report["wet_lab_validation_plan"])
        lines.extend(
            [
                "",
                "## 8. Limitations",
            ]
        )
        lines.extend(f"- {item}" for item in report["limitations"])
        return "\n".join(lines)

    @staticmethod
    def _risk_assessment(top_variants: list[EnzymeVariantRecord]) -> str:
        if not top_variants:
            return "No variants have been generated; risk assessment is pending."
        average_risk = sum(variant.mutation_risk_score or 0 for variant in top_variants) / len(top_variants)
        return (
            f"Top candidates have an average mutation risk score of {average_risk:.2f}. "
            "Treat these scores as triage signals and avoid direct catalytic-residue mutation without literature or assay support."
        )

    @staticmethod
    def _wet_lab_plan() -> list[str]:
        return [
            "Express and purify wild type plus top variants side-by-side.",
            "Measure activity against the selected substrate under target pH, temperature, salinity, and solvent conditions.",
            "Confirm thermostability and retained activity across process-relevant time windows.",
            "Sequence-confirm constructs and include negative, wild-type, and known-positive controls where available.",
        ]

    @staticmethod
    def _limitations() -> list[str]:
        return [
            "This MVP uses sequence and active-site heuristics for prioritization, not experimental proof.",
            "Docking, molecular dynamics, QM/MM, pKa simulation, FEP, and wet-lab assays are not performed here.",
            "Do not mutate known catalytic residues unless literature or experiments support the hypothesis.",
        ]

    def _state(self, project_id: str) -> ProjectState:
        if project_id not in self._projects:
            raise self._not_found("Project")
        return self._projects[project_id]

    @staticmethod
    def _not_found(name: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} not found.")

    @staticmethod
    def _id() -> str:
        return str(uuid.uuid4())


project_workflow_service = ProjectWorkflowService()
