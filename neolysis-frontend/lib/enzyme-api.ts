const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface TargetConditions {
  temperature_c?: number;
  ph?: number;
  salinity_m_m?: number;
  solvent_exposure?: string;
  use_case?: string;
  notes?: string;
}

export interface VariantCandidate {
  variant_id: string;
  name?: string;
  sequence?: string;
  mutations?: string[];
}

export interface SequenceValidationResult {
  valid: boolean;
  name?: string | null;
  cleaned_sequence: string;
  sequence_length: number;
  invalid_residues: string[];
  warnings: string[];
  detected_format: string;
}

export interface ProteinFeatureResult {
  sequence_length: number;
  amino_acid_composition: Record<string, number>;
  amino_acid_percent: Record<string, number>;
  molecular_weight: number;
  gravy?: number | null;
  aromaticity?: number | null;
  instability_index?: number | null;
  isoelectric_point?: number | null;
  method: string;
  warnings: string[];
}

export interface PropertyIndicator {
  score: number;
  label: string;
  explanation: string;
}

export interface PropertyScoreResult {
  thermostability: PropertyIndicator;
  ph_fit: PropertyIndicator;
  solubility: PropertyIndicator;
  condition_fit: PropertyIndicator;
  industrial_fit_score: number;
  risk_flags: string[];
  confidence: number;
  method: string;
  model_version: string;
  limitations: string[];
}

export interface EnzymePrediction {
  predicted_family: string;
  predicted_ec_class?: string | null;
  confidence: number;
  explanation: string;
  evidence: string[];
  method: string;
  model_version: string;
  limitations: string[];
}

export interface RankedVariant {
  rank: number;
  variant_id: string;
  name?: string | null;
  mutation_summary: string;
  predicted_fit_score: number;
  risk_score: number;
  confidence: number;
  wet_lab_priority: string;
  explanation: string;
  risk_flags: string[];
}

export interface VariantRankResponse {
  ranked_variants: RankedVariant[];
  limitations: string[];
}

export interface AgentToolCall {
  name: string;
  status: string;
  summary: string;
}

export interface AgentAnalysisResponse {
  agent_plan: string[];
  tool_calls: AgentToolCall[];
  structured_analysis: {
    sequence?: {
      validation: SequenceValidationResult;
      features?: ProteinFeatureResult | null;
    };
    enzyme_function?: {
      prediction: EnzymePrediction;
    };
    property_scoring?: PropertyScoreResult;
    variant_ranking?: VariantRankResponse | null;
    report?: Record<string, unknown>;
  };
  final_report: string;
  limitations: string[];
}

async function postJson<TResponse, TBody>(path: string, body: TBody): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const detail = await response.json();
      message = typeof detail.detail === 'string'
        ? detail.detail
        : detail.detail?.message || message;
    } catch {
      // Keep the generic message when the backend does not return JSON.
    }
    throw new Error(message);
  }

  return response.json() as Promise<TResponse>;
}

export function analyzeSequence(body: {
  sequence: string;
  target_conditions: TargetConditions;
  variants?: VariantCandidate[];
  user_question?: string;
  enzyme_class_hint?: string;
}) {
  return postJson<AgentAnalysisResponse, typeof body>('/agents/analyze', body);
}

export function rankVariants(body: {
  wild_type_sequence: string;
  variants: VariantCandidate[];
  target_conditions: TargetConditions;
}) {
  return postJson<VariantRankResponse, typeof body>('/variants/rank', body);
}

export const sampleEnzymeSequence =
  'MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGEENFKALVLIAFAQYLQQCPFEDH' +
  'VKLVNEVTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEPERNECFL' +
  'SHKDDSPDLPKLKPDPNTLCDEFKADEKKFWGKYLYEIARRHPYFYAPELLYYANKYNGVFQECC';
