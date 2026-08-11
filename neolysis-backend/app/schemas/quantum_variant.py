from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MutationOption(BaseModel):
    substitution: str = Field(..., description="Mutation code e.g. 'A123V' or 'WT' for wild-type")
    score_contribution: float = Field(0.0, description="Estimated property score improvement")
    risk_penalty: float = Field(0.0, description="Estimated mutation risk/destabilization penalty")
    is_wildtype: bool = Field(False, description="True if this option represents keeping wild-type (no mutation)")


class MutationPosition(BaseModel):
    position_id: int = Field(..., description="1-indexed position identifier")
    position_name: str = Field(..., description="Residue position label e.g. 'Pos 142 (Active Loop)'")
    options: List[MutationOption] = Field(..., min_length=1, description="Available substitution choices at this position")


class IncompatiblePair(BaseModel):
    pos_a: int = Field(..., description="First position ID")
    sub_a: str = Field(..., description="First substitution code")
    pos_b: int = Field(..., description="Second position ID")
    sub_b: str = Field(..., description="Second substitution code")
    penalty_cost: float = Field(10.0, description="Penalty cost incurred if both substitutions are selected")


class QuantumVariantRankRequest(BaseModel):
    positions: List[MutationPosition] = Field(..., min_length=1, description="List of candidate mutation positions")
    incompatible_pairs: List[IncompatiblePair] = Field(default_factory=list, description="Mutually exclusive substitution pairs")
    max_mutations: Optional[int] = Field(None, description="Maximum number of non-WT mutations allowed")
    coverage_penalty_weight: float = Field(20.0, description="Penalty for failing to select exactly 1 option per position")
    interaction_penalty_weight: float = Field(15.0, description="Penalty weight for incompatible mutation pairs")
    max_mutations_penalty_weight: float = Field(15.0, description="Penalty for exceeding max non-WT mutations limit")
    qaoa_reps: int = Field(1, ge=1, le=4, description="QAOA depth parameter p (layers)")
    qaoa_max_iter: int = Field(60, ge=10, le=200, description="Max iterations for classical QAOA parameter optimizer")


class SelectedMutation(BaseModel):
    position_id: int
    position_name: str
    substitution: str
    score_contribution: float
    risk_penalty: float
    is_wildtype: bool


class SolverResult(BaseModel):
    solver_name: str = Field(..., description="Accurate solver identifier e.g. 'Qiskit Aer SamplerV2 / Statevector QAOA'")
    solver_type: str = Field(..., description="'quantum' or 'classical'")
    selected_mutations: List[SelectedMutation] = Field(default_factory=list)
    total_property_score: float = Field(0.0, description="Sum of selected property score contributions")
    total_mutation_risk: float = Field(0.0, description="Sum of selected mutation risk penalties")
    constraint_violations: List[str] = Field(default_factory=list, description="Plain text list of any unmet constraints")
    penalty_cost: float = Field(0.0, description="Total penalty cost incurred from unmet constraints")
    honest_net_score: float = Field(0.0, description="Honest total score = total_property_score - total_mutation_risk - penalty_cost")
    qubo_energy: float = Field(0.0, description="Evaluated QUBO objective value for the binary vector")
    solve_time_ms: float = Field(..., description="Pure solver computation time in milliseconds (excluding HTTP/IO)")
    is_feasible: bool = Field(True, description="True if no constraint penalties were violated")
    qubit_count: int = Field(..., description="Total binary decision variables / qubits in problem formulation")
    bitstring: str = Field("", description="Binary vector bitstring representation of decision variables")


class CorrectnessCheck(BaseModel):
    test_case_qubits: int = Field(4, description="Qubit size of tiny verification test case")
    exact_qubo_energy: float = Field(..., description="Ground truth optimal QUBO energy from exact solver")
    qaoa_qubo_energy: float = Field(..., description="QAOA evaluated QUBO energy on test case")
    energy_match: bool = Field(..., description="True if QAOA energy matches exact solver within tolerance")
    energy_gap_percent: float = Field(..., description="Percentage gap between QAOA and exact energy")
    check_time_ms: float = Field(..., description="Time taken to execute verification check in ms")
    verification_log: str = Field(..., description="Verification result trace log")


class QuantumVariantRankResponse(BaseModel):
    quantum_result: SolverResult
    classical_result: SolverResult
    correctness_check: CorrectnessCheck
    problem_summary: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
