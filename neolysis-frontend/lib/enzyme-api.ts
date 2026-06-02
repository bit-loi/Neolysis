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

async function getJson<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`);

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
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

export interface ProjectRecord {
  id: string;
  name: string;
  description?: string | null;
  enzyme_target?: string | null;
  enzyme_name?: string | null;
  objective?: string | null;
  organism_source?: string | null;
  target_industry?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface EnzymeSequenceRecord {
  id: string;
  project_id: string;
  sequence: string;
  sequence_length: number;
  length: number;
  molecular_weight?: number | null;
  pI?: number | null;
  instability_index?: number | null;
  GRAVY?: number | null;
  aromaticity?: number | null;
  is_valid: boolean;
  validation_errors: string[];
  validation: SequenceValidationResult;
  feature_json?: ProteinFeatureResult | null;
}

export interface EnzymeStructureRecord {
  id: string;
  project_id: string;
  source_type: string;
  source?: string | null;
  pdb_id?: string | null;
  alphafold_id?: string | null;
  chain_id?: string | null;
  raw_pdb_text?: string | null;
  uploaded_pdb_path?: string | null;
  storage_path?: string | null;
  structure_notes?: string | null;
  confidence_notes: string[];
}

export interface SubstrateRecord {
  id: string;
  project_id: string;
  name: string;
  smiles: string;
  sdf_path?: string | null;
  role: string;
  notes?: string | null;
  validation_notes: string[];
}

export interface ActiveSiteRecord {
  id: string;
  project_id: string;
  structure_id: string;
  name: string;
  residue_list: string[];
  residue_positions: number[];
  nearby_residues: string[];
  mutation_candidate_residues: string[];
  protected_residues: string[];
  selection_method: string;
  notes?: string | null;
  warnings: string[];
}

export interface EnzymeVariantRecord {
  id: string;
  project_id: string;
  mutation_label: string;
  wild_type_residue: string;
  position: number;
  mutant_residue: string;
  reason: string;
  active_site_distance_proxy?: number | null;
  sequence_property_score?: number | null;
  active_site_relevance_score?: number | null;
  stability_proxy_score?: number | null;
  binding_proxy_score?: number | null;
  docking_score_normalized?: number | null;
  mutation_risk_score?: number | null;
  final_score?: number | null;
  explanation: string;
  warnings: string[];
}

export interface AnalysisReportRecord {
  id: string;
  project_id: string;
  report_type: string;
  summary: string;
  top_variants: Record<string, unknown>[];
  wet_lab_plan: string[];
  limitations: string[];
  markdown_report: string;
  report_json: Record<string, unknown>;
}

export interface DockingJobRecord {
  id: string;
  project_id: string;
  structure_id?: string | null;
  substrate_id?: string | null;
  status: string;
  grid_center?: Record<string, number> | null;
  grid_size?: Record<string, number> | null;
  docking_score?: number | null;
  output_pose_path?: string | null;
  interacting_residues: string[];
  notes?: string | null;
}

export interface ProjectDetailResponse {
  project: ProjectRecord;
  sequence?: EnzymeSequenceRecord | null;
  structures: EnzymeStructureRecord[];
  substrates: SubstrateRecord[];
  active_sites: ActiveSiteRecord[];
  variants: EnzymeVariantRecord[];
  docking_jobs: DockingJobRecord[];
  reports: AnalysisReportRecord[];
}

export function createProject(body: {
  name: string;
  description?: string;
  enzyme_target?: string;
  enzyme_name?: string;
  objective?: string;
  organism_source?: string;
  target_industry?: string;
}) {
  return postJson<ProjectRecord, typeof body>('/projects', body);
}

export function listProjects() {
  return getJson<ProjectRecord[]>('/projects');
}

export function getProject(projectId: string) {
  return getJson<ProjectDetailResponse>(`/projects/${projectId}`);
}

export function setProjectSequence(projectId: string, body: { sequence: string; name?: string }) {
  return postJson<EnzymeSequenceRecord, typeof body>(`/projects/${projectId}/sequence`, body);
}

export function setProjectStructure(projectId: string, body: {
  source_type: string;
  source?: string;
  pdb_id?: string;
  alphafold_id?: string;
  chain_id?: string;
  raw_pdb_text?: string;
  uploaded_pdb_path?: string;
  structure_notes?: string;
}) {
  return postJson<EnzymeStructureRecord, typeof body>(`/projects/${projectId}/structure`, body);
}

export function addProjectSubstrate(projectId: string, body: {
  name: string;
  smiles: string;
  sdf_path?: string;
  role: string;
  notes?: string;
}) {
  return postJson<SubstrateRecord, typeof body>(`/projects/${projectId}/substrates`, body);
}

export function addProjectActiveSite(projectId: string, body: {
  structure_id: string;
  name: string;
  residues: string[];
  notes?: string;
}) {
  return postJson<ActiveSiteRecord, typeof body>(`/projects/${projectId}/active-site`, body);
}

export function generateProjectVariants(projectId: string, body: {
  max_variants: number;
  allow_catalytic_mutations?: boolean;
  target_residues?: string[];
}) {
  return postJson<EnzymeVariantRecord[], typeof body>(`/projects/${projectId}/variants/generate`, body);
}

export function addProjectDockingJob(projectId: string, body: {
  structure_id?: string;
  substrate_id?: string;
  status: string;
  grid_center?: Record<string, number>;
  grid_size?: Record<string, number>;
  docking_score?: number;
  output_pose_path?: string;
  interacting_residues?: string[];
  notes?: string;
}) {
  return postJson<DockingJobRecord, typeof body>(`/projects/${projectId}/docking-jobs`, body);
}

export function generateProjectReport(projectId: string) {
  return postJson<AnalysisReportRecord, Record<string, never>>(
    `/projects/${projectId}/reports/generate`,
    {},
  );
}

export const sampleEnzymeSequence =
  'MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGEENFKALVLIAFAQYLQQCPFEDH' +
  'VKLVNEVTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEPERNECFL' +
  'SHKDDSPDLPKLKPDPNTLCDEFKADEKKFWGKYLYEIARRHPYFYAPELLYYANKYNGVFQECC';
