-- Neolysis PostgreSQL migration seed
-- Purpose: relational source-of-truth schema for enzyme engineering projects,
-- docking outputs, evidence, reports, and graph-ready relations.
--
-- Notes:
-- - JSON/JSONB remains the data exchange and worker-output format.
-- - TOON, if enabled elsewhere, must stay an internal LLM prompt compression layer.
-- - This file is raw PostgreSQL SQL for Supabase/Postgres review and migration.
-- - The existing SQLAlchemy/Alembic setup can later translate these tables into ORM
--   models or Alembic Python revisions when persistence is wired into the services.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Optional for future embedding/literature search:
-- CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- V1: Core Product Layer
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NULL,
    name TEXT NOT NULL,
    description TEXT,
    objective TEXT,
    target_industry TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enzymes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    enzyme_class TEXT,
    ec_number TEXT,
    organism TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enzyme_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enzyme_id UUID REFERENCES enzymes(id) ON DELETE CASCADE,
    sequence TEXT NOT NULL,
    sequence_length INT,
    molecular_weight FLOAT,
    pi FLOAT,
    gravy FLOAT,
    aromaticity FLOAT,
    instability_index FLOAT,
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors JSONB DEFAULT '[]'::jsonb,
    feature_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enzyme_structures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enzyme_id UUID REFERENCES enzymes(id) ON DELETE CASCADE,
    sequence_id UUID REFERENCES enzyme_sequences(id) ON DELETE SET NULL,
    source_type TEXT NOT NULL,
    pdb_id TEXT,
    chain_id TEXT,
    storage_path TEXT,
    raw_pdb_text TEXT,
    confidence_score FLOAT,
    structure_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS substrates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    smiles TEXT,
    role TEXT DEFAULT 'substrate',
    formula TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS residues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    structure_id UUID REFERENCES enzyme_structures(id) ON DELETE CASCADE,
    chain_id TEXT,
    residue_number INT NOT NULL,
    residue_name TEXT NOT NULL,
    one_letter_code TEXT,
    residue_label TEXT NOT NULL,
    x FLOAT,
    y FLOAT,
    z FLOAT,
    annotation JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS active_sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    structure_id UUID REFERENCES enzyme_structures(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    selection_method TEXT DEFAULT 'manual',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS active_site_residues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    active_site_id UUID REFERENCES active_sites(id) ON DELETE CASCADE,
    residue_id UUID REFERENCES residues(id) ON DELETE CASCADE,
    role TEXT,
    is_catalytic BOOLEAN DEFAULT FALSE,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS enzyme_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enzyme_id UUID REFERENCES enzymes(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    mutation_label TEXT NOT NULL,
    wild_type_residue TEXT NOT NULL,
    position INT NOT NULL,
    mutant_residue TEXT NOT NULL,
    chain_id TEXT,
    reason TEXT,
    explanation TEXT,
    sequence_property_score FLOAT,
    active_site_relevance_score FLOAT,
    stability_proxy_score FLOAT,
    binding_proxy_score FLOAT,
    docking_score_normalized FLOAT,
    mutation_risk_score FLOAT,
    final_score FLOAT,
    status TEXT DEFAULT 'candidate',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS variant_residue_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variant_id UUID REFERENCES enzyme_variants(id) ON DELETE CASCADE,
    residue_id UUID REFERENCES residues(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    distance_to_active_site FLOAT,
    notes TEXT
);

-- ============================================================================
-- V2: Computation Layer
-- ============================================================================

CREATE TABLE IF NOT EXISTS docking_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    structure_id UUID REFERENCES enzyme_structures(id) ON DELETE CASCADE,
    substrate_id UUID REFERENCES substrates(id) ON DELETE CASCADE,
    variant_id UUID REFERENCES enzyme_variants(id) ON DELETE SET NULL,
    engine TEXT DEFAULT 'quickvina2',
    compute_backend TEXT DEFAULT 'local',
    status TEXT DEFAULT 'pending',
    grid_center_x FLOAT NOT NULL,
    grid_center_y FLOAT NOT NULL,
    grid_center_z FLOAT NOT NULL,
    grid_size_x FLOAT NOT NULL,
    grid_size_y FLOAT NOT NULL,
    grid_size_z FLOAT NOT NULL,
    exhaustiveness INT DEFAULT 4,
    receptor_source_path TEXT,
    receptor_storage_path TEXT,
    ligand_source_smiles TEXT,
    ligand_storage_path TEXT,
    remote_kernel_ref TEXT,
    remote_output_path TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS docking_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    docking_job_id UUID REFERENCES docking_jobs(id) ON DELETE CASCADE,
    binding_affinity FLOAT,
    pose_rank INT,
    rmsd_lb FLOAT,
    rmsd_ub FLOAT,
    output_pose_path TEXT,
    output_log_path TEXT,
    raw_engine_output TEXT,
    distance_cutoff_angstrom FLOAT DEFAULT 4.0,
    interacting_residues_json JSONB DEFAULT '[]'::jsonb,
    execution_backend TEXT DEFAULT 'local',
    remote_kernel_ref TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS residue_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    docking_result_id UUID REFERENCES docking_results(id) ON DELETE CASCADE,
    residue_id UUID REFERENCES residues(id) ON DELETE CASCADE,
    min_distance FLOAT,
    contact_type TEXT DEFAULT 'distance_based',
    ligand_atom TEXT,
    protein_atom TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- V3: Evidence + Reports
-- ============================================================================

CREATE TABLE IF NOT EXISTS literature_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    authors TEXT,
    journal TEXT,
    year INT,
    doi TEXT,
    url TEXT,
    abstract TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evidence_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,
    source_id UUID NOT NULL,
    target_type TEXT NOT NULL,
    target_id UUID NOT NULL,
    evidence_type TEXT NOT NULL,
    relationship TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    reference_id UUID REFERENCES literature_references(id) ON DELETE SET NULL,
    notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analysis_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL,
    summary TEXT,
    report_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- V4: Knowledge Graph-Lite Layer
-- ============================================================================

CREATE TABLE IF NOT EXISTS kg_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type TEXT NOT NULL,
    entity_table TEXT NOT NULL,
    entity_id UUID NOT NULL,
    label TEXT NOT NULL,
    description TEXT,
    properties JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(entity_table, entity_id)
);

CREATE TABLE IF NOT EXISTS kg_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id UUID REFERENCES kg_nodes(id) ON DELETE CASCADE,
    predicate TEXT NOT NULL,
    target_node_id UUID REFERENCES kg_nodes(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 1.0,
    evidence_id UUID REFERENCES evidence_links(id) ON DELETE SET NULL,
    properties JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Helpful indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_enzymes_project_id ON enzymes(project_id);
CREATE INDEX IF NOT EXISTS idx_enzyme_structures_enzyme_id ON enzyme_structures(enzyme_id);
CREATE INDEX IF NOT EXISTS idx_residues_structure_id ON residues(structure_id);
CREATE INDEX IF NOT EXISTS idx_residues_label ON residues(residue_label);
CREATE INDEX IF NOT EXISTS idx_active_sites_project_id ON active_sites(project_id);
CREATE INDEX IF NOT EXISTS idx_enzyme_variants_project_id ON enzyme_variants(project_id);
CREATE INDEX IF NOT EXISTS idx_enzyme_variants_final_score ON enzyme_variants(final_score DESC);
CREATE INDEX IF NOT EXISTS idx_docking_jobs_project_id ON docking_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_docking_jobs_status ON docking_jobs(status);
CREATE INDEX IF NOT EXISTS idx_docking_results_job_id ON docking_results(docking_job_id);
CREATE INDEX IF NOT EXISTS idx_residue_contacts_result_id ON residue_contacts(docking_result_id);
CREATE INDEX IF NOT EXISTS idx_evidence_links_target ON evidence_links(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_entity ON kg_nodes(entity_table, entity_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_predicate ON kg_edges(predicate);

-- ============================================================================
-- Example analysis queries
-- ============================================================================

-- Top variants with strong docking hypothesis and low mutation risk.
-- SELECT
--     v.mutation_label,
--     v.final_score,
--     v.mutation_risk_score,
--     dr.binding_affinity,
--     s.name AS substrate_name
-- FROM enzyme_variants v
-- JOIN docking_jobs dj ON dj.variant_id = v.id
-- JOIN docking_results dr ON dr.docking_job_id = dj.id
-- JOIN substrates s ON s.id = dj.substrate_id
-- WHERE v.project_id = $1
-- ORDER BY v.final_score DESC
-- LIMIT 10;

-- Residues most frequently contacted by docked ligands.
-- SELECT
--     r.residue_label,
--     COUNT(*) AS contact_count,
--     AVG(rc.min_distance) AS avg_distance
-- FROM residue_contacts rc
-- JOIN residues r ON r.id = rc.residue_id
-- GROUP BY r.residue_label
-- ORDER BY contact_count DESC;

-- Variants near active site that have not been docked yet.
-- SELECT
--     v.id,
--     v.mutation_label,
--     v.active_site_relevance_score
-- FROM enzyme_variants v
-- LEFT JOIN docking_jobs dj ON dj.variant_id = v.id
-- WHERE dj.id IS NULL
-- ORDER BY v.active_site_relevance_score DESC;
