export interface MutationOption {
  substitution: string;
  score_contribution: number;
  risk_penalty: number;
  is_wildtype: boolean;
}

export interface MutationPosition {
  position_id: number;
  position_name: string;
  options: MutationOption[];
}

export interface IncompatiblePair {
  pos_a: number;
  sub_a: string;
  pos_b: number;
  sub_b: string;
  penalty_cost: number;
}

export interface QuantumVariantRankRequest {
  positions: MutationPosition[];
  incompatible_pairs?: IncompatiblePair[];
  max_mutations?: number | null;
  coverage_penalty_weight?: number;
  interaction_penalty_weight?: number;
  max_mutations_penalty_weight?: number;
  qaoa_reps?: number;
  qaoa_max_iter?: number;
}

export interface SelectedMutation {
  position_id: number;
  position_name: string;
  substitution: string;
  score_contribution: number;
  risk_penalty: number;
  is_wildtype: boolean;
}

export interface SolverResult {
  solver_name: string;
  solver_type: 'quantum' | 'classical';
  selected_mutations: SelectedMutation[];
  total_property_score: number;
  total_mutation_risk: number;
  constraint_violations: string[];
  penalty_cost: number;
  honest_net_score: number;
  qubo_energy: number;
  solve_time_ms: number;
  is_feasible: boolean;
  qubit_count: number;
  bitstring: string;
}

export interface CorrectnessCheck {
  test_case_qubits: number;
  exact_qubo_energy: number;
  qaoa_qubo_energy: number;
  energy_match: boolean;
  energy_gap_percent: number;
  check_time_ms: number;
  verification_log: string;
}

export interface QuantumVariantRankResponse {
  quantum_result: SolverResult;
  classical_result: SolverResult;
  correctness_check: CorrectnessCheck;
  problem_summary: {
    num_positions: number;
    num_qubits: number;
    max_mutations_allowed?: number | null;
    num_incompatible_pairs: number;
  };
  limitations: string[];
}

export interface PresetScenario {
  id: string;
  name: string;
  description: string;
  target_enzyme: string;
  request: QuantumVariantRankRequest;
}

export type QuantumTab = 'comparison' | 'qubo' | 'disclaimer';
