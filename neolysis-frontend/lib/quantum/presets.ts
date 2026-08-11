import { PresetScenario } from './types';

export const PRESET_QUANTUM_SCENARIOS: PresetScenario[] = [
  {
    id: 'thermostable_protease',
    name: 'Thermostable Protease Engineering (4 Positions)',
    description:
      'Optimizes detergent-stable alkaline protease for elevated temperatures (65 C) across 4 surface/loop positions.',
    target_enzyme: 'Alkaline Serine Protease (Subtilisin family)',
    request: {
      positions: [
        {
          position_id: 1,
          position_name: 'Pos 142 (Flex Loop Alpha)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'A142V', score_contribution: 0.85, risk_penalty: 0.15, is_wildtype: false },
            { substitution: 'A142L', score_contribution: 0.6, risk_penalty: 0.1, is_wildtype: false },
          ],
        },
        {
          position_id: 2,
          position_name: 'Pos 205 (Surface Salt Bridge)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'E205K', score_contribution: 0.9, risk_penalty: 0.2, is_wildtype: false },
            { substitution: 'E205R', score_contribution: 0.7, risk_penalty: 0.12, is_wildtype: false },
          ],
        },
        {
          position_id: 3,
          position_name: 'Pos 254 (Substrate Binding Pocket)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'N254D', score_contribution: 0.75, risk_penalty: 0.25, is_wildtype: false },
          ],
        },
        {
          position_id: 4,
          position_name: 'Pos 310 (Hydrophobic Core)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'I310F', score_contribution: 0.8, risk_penalty: 0.3, is_wildtype: false },
            { substitution: 'I310W', score_contribution: 0.4, risk_penalty: 0.45, is_wildtype: false },
          ],
        },
      ],
      incompatible_pairs: [
        { pos_a: 1, sub_a: 'A142V', pos_b: 4, sub_b: 'I310W', penalty_cost: 15.0 },
      ],
      max_mutations: 3,
      coverage_penalty_weight: 20.0,
      interaction_penalty_weight: 15.0,
      qaoa_reps: 1,
      qaoa_max_iter: 60,
    },
  },
  {
    id: 'alkaline_cellulase',
    name: 'Alkaline Cellulase pH Shift (3 Positions)',
    description:
      'Targets active-site rim residues to shift optimal activity from pH 6.0 to pH 10.5 for industrial textile processing.',
    target_enzyme: 'Endo-1,4-beta-glucanase',
    request: {
      positions: [
        {
          position_id: 1,
          position_name: 'Pos 88 (Catalytic Rim)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'D88H', score_contribution: 0.95, risk_penalty: 0.18, is_wildtype: false },
          ],
        },
        {
          position_id: 2,
          position_name: 'Pos 112 (Tunnel Entry)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'K112R', score_contribution: 0.65, risk_penalty: 0.08, is_wildtype: false },
            { substitution: 'K112Q', score_contribution: 0.4, risk_penalty: 0.1, is_wildtype: false },
          ],
        },
        {
          position_id: 3,
          position_name: 'Pos 175 (H-bonding Network)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'S175T', score_contribution: 0.5, risk_penalty: 0.05, is_wildtype: false },
          ],
        },
      ],
      incompatible_pairs: [],
      max_mutations: 2,
      coverage_penalty_weight: 20.0,
      interaction_penalty_weight: 15.0,
      qaoa_reps: 1,
      qaoa_max_iter: 50,
    },
  },
  {
    id: 'lipase_enantioselectivity',
    name: 'Lipase Active Site Engineering (5 Positions)',
    description:
      'Combinatorial active site reshaping for biocatalytic esterification with 5 candidate mutation positions (12 qubits).',
    target_enzyme: 'Candida antarctica Lipase B (CALB)',
    request: {
      positions: [
        {
          position_id: 1,
          position_name: 'Pos 105 (Stereospecificity Pocket)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'W104A', score_contribution: 0.88, risk_penalty: 0.22, is_wildtype: false },
            { substitution: 'W104F', score_contribution: 0.72, risk_penalty: 0.14, is_wildtype: false },
          ],
        },
        {
          position_id: 2,
          position_name: 'Pos 140 (Oxyanion Hole Support)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'T138A', score_contribution: 0.6, risk_penalty: 0.15, is_wildtype: false },
          ],
        },
        {
          position_id: 3,
          position_name: 'Pos 190 (Entrance Flap)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'L190I', score_contribution: 0.45, risk_penalty: 0.08, is_wildtype: false },
            { substitution: 'L190V', score_contribution: 0.55, risk_penalty: 0.12, is_wildtype: false },
          ],
        },
        {
          position_id: 4,
          position_name: 'Pos 278 (Hydrophobic Wall)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'V278L', score_contribution: 0.7, risk_penalty: 0.18, is_wildtype: false },
          ],
        },
        {
          position_id: 5,
          position_name: 'Pos 290 (Substrate Channel)',
          options: [
            { substitution: 'WT', score_contribution: 0.0, risk_penalty: 0.0, is_wildtype: true },
            { substitution: 'I285L', score_contribution: 0.5, risk_penalty: 0.1, is_wildtype: false },
          ],
        },
      ],
      incompatible_pairs: [
        { pos_a: 1, sub_a: 'W104A', pos_b: 4, sub_b: 'V278L', penalty_cost: 15.0 },
      ],
      max_mutations: 3,
      coverage_penalty_weight: 20.0,
      interaction_penalty_weight: 15.0,
      qaoa_reps: 1,
      qaoa_max_iter: 70,
    },
  },
];
