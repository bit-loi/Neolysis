'use client';
/* eslint-disable @typescript-eslint/no-explicit-any, react-hooks/set-state-in-effect */

import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import {
  Activity,
  Beaker,
  Box,
  FileText,
  FlaskConical,
  GitBranch,
  Layers3,
  Save,
} from 'lucide-react';
import {
  ActiveSiteRecord,
  AnalysisReportRecord,
  EnzymeStructureRecord,
  EnzymeVariantRecord,
  ProjectDetailResponse,
  ProjectRecord,
  addProjectActiveSite,
  addProjectSubstrate,
  createProject,
  generateProjectReport,
  generateProjectVariants,
  getProject,
  listProjects,
  sampleEnzymeSequence,
  setProjectSequence,
  setProjectStructure,
} from '@/lib/enzyme-api';

declare global {
  interface Window {
    $3Dmol: any;
  }
}

const SAMPLE_PDB = `ATOM      1  N   SER A  10      11.104  13.207  14.110  1.00 20.00           N
ATOM      2  CA  SER A  10      12.560  13.200  14.320  1.00 20.00           C
ATOM      3  C   SER A  10      13.083  11.820  14.725  1.00 20.00           C
ATOM      4  N   HIS A  57      15.104  10.207  12.110  1.00 20.00           N
ATOM      5  CA  HIS A  57      15.960  10.900  11.130  1.00 20.00           C
ATOM      6  N   ASP A 102      18.104  12.207  10.110  1.00 20.00           N
ATOM      7  CA  ASP A 102      18.620  13.430   9.540  1.00 20.00           C
END`;

export default function StructurePage() {
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [project, setProject] = useState<ProjectDetailResponse | null>(null);
  const [projectName, setProjectName] = useState('Protease structure-aware prioritization');
  const [enzymeTarget, setEnzymeTarget] = useState('alkaline protease candidate');
  const [organismSource, setOrganismSource] = useState('source organism TBD');
  const [sequence, setSequence] = useState(sampleEnzymeSequence);
  const [pdbText, setPdbText] = useState(SAMPLE_PDB);
  const [pdbId, setPdbId] = useState('');
  const [chainId, setChainId] = useState('A');
  const [activeSite, setActiveSite] = useState('S10, H57, D102');
  const [substrateName, setSubstrateName] = useState('model ester substrate');
  const [smiles, setSmiles] = useState('CCOC(=O)C');
  const [substrateRole, setSubstrateRole] = useState('substrate');
  const [variants, setVariants] = useState<EnzymeVariantRecord[]>([]);
  const [report, setReport] = useState<AnalysisReportRecord | null>(null);
  const [status, setStatus] = useState('Create or select a project to begin.');
  const [error, setError] = useState<string | null>(null);
  const activeStructure = project?.structures[0] ?? null;

  const refreshProjects = useCallback(async () => {
    setProjects(await listProjects());
  }, []);

  const refreshProject = useCallback(async (projectId: string) => {
    const detail = await getProject(projectId);
    setProject(detail);
    setVariants(detail.variants);
    setReport(detail.reports[0] ?? null);
  }, []);

  useEffect(() => {
    refreshProjects().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load projects'));
  }, [refreshProjects]);

  const run = async (label: string, action: () => Promise<void>) => {
    setError(null);
    setStatus(label);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
    }
  };

  const handleCreateProject = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    run('Creating project...', async () => {
      const created = await createProject({
        name: projectName,
        enzyme_target: enzymeTarget,
        enzyme_name: enzymeTarget,
        objective: 'Prioritize mutations before wet-lab validation',
        organism_source: organismSource,
        target_industry: 'industrial biotechnology',
      });
      await refreshProjects();
      await refreshProject(created.id);
      setStatus('Project ready.');
    });
  };

  const currentProjectId = project?.project.id;

  const saveSequence = () => {
    if (!currentProjectId) return;
    run('Saving sequence and extracting features...', async () => {
      await setProjectSequence(currentProjectId, { sequence });
      await refreshProject(currentProjectId);
      setStatus('Sequence profile saved.');
    });
  };

  const saveStructure = () => {
    if (!currentProjectId) return;
    run('Saving structure record...', async () => {
      await setProjectStructure(currentProjectId, {
        source_type: 'uploaded_pdb',
        chain_id: chainId,
        raw_pdb_text: pdbText,
        structure_notes: 'MVP uploaded/pasted PDB text for visualization and active-site context.',
      });
      await refreshProject(currentProjectId);
      setStatus('Structure saved.');
    });
  };

  const fetchPdb = () => {
    const normalized = pdbId.trim().toUpperCase();
    if (!normalized) return;
    run('Fetching PDB text...', async () => {
      const response = await fetch(`https://files.rcsb.org/download/${normalized}.pdb`);
      if (!response.ok) throw new Error(`PDB ${normalized} could not be fetched.`);
      setPdbText(await response.text());
      setStatus(`Fetched PDB ${normalized}. Review chain and save the structure.`);
    });
  };

  const saveSubstrate = () => {
    if (!currentProjectId) return;
    run('Saving substrate...', async () => {
      await addProjectSubstrate(currentProjectId, {
        name: substrateName,
        smiles,
        role: substrateRole,
        notes: 'Registered for future docking-aware scoring.',
      });
      await refreshProject(currentProjectId);
      setStatus('Substrate saved.');
    });
  };

  const saveActiveSite = () => {
    if (!currentProjectId || !activeStructure) return;
    run('Saving active-site definition...', async () => {
      await addProjectActiveSite(currentProjectId, {
        structure_id: activeStructure.id,
        name: 'Catalytic pocket',
        residues: activeSite.split(',').map((item) => item.trim()).filter(Boolean),
        notes: 'Manual active-site definition for MVP structure-aware ranking.',
      });
      await refreshProject(currentProjectId);
      setStatus('Active site saved.');
    });
  };

  const generateVariants = () => {
    if (!currentProjectId) return;
    run('Generating structure-aware variants...', async () => {
      const result = await generateProjectVariants(currentProjectId, { max_variants: 12 });
      setVariants(result);
      await refreshProject(currentProjectId);
      setStatus('Variants generated.');
    });
  };

  const generateReport = () => {
    if (!currentProjectId) return;
    run('Generating decision memo...', async () => {
      const result = await generateProjectReport(currentProjectId);
      setReport(result);
      await refreshProject(currentProjectId);
      setStatus('Decision memo generated.');
    });
  };

  return (
    <div className="min-h-screen bg-[#f5f5f0] pt-28 pb-16 text-[#171717] grain-overlay">
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-[#5BA8B9]">
              Structure-Aware MVP
            </p>
            <h1 className="mt-3 font-serif text-4xl font-bold tracking-tight sm:text-5xl">
              Enzyme structure workspace
            </h1>
            <p className="mt-4 text-lg leading-relaxed text-gray-700">
              Connect sequence, PDB context, active-site residues, substrates, and explainable variant hypotheses.
            </p>
          </div>
          <StatusBadge status={status} error={error} />
        </div>

        <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="space-y-5">
            <Panel title="Project" icon={<Layers3 className="h-5 w-5" />}>
              <form onSubmit={handleCreateProject} className="space-y-3">
                <input
                  value={projectName}
                  onChange={(event) => setProjectName(event.target.value)}
                  className="w-full border border-gray-300 bg-[#fbfbf8] px-3 py-2 text-sm outline-none focus:border-[#5BA8B9]"
                />
                <Input label="Enzyme target" value={enzymeTarget} onChange={setEnzymeTarget} />
                <Input label="Organism/source" value={organismSource} onChange={setOrganismSource} />
                <button type="submit" className="inline-flex w-full items-center justify-center gap-2 border border-black px-4 py-2 text-sm font-medium">
                  <Save className="h-4 w-4" />
                  Create project
                </button>
              </form>
              <select
                value={project?.project.id ?? ''}
                onChange={(event) => event.target.value && refreshProject(event.target.value)}
                className="mt-4 w-full border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-[#5BA8B9]"
              >
                <option value="">Select existing project</option>
                {projects.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </Panel>

            <Panel title="Substrate" icon={<Beaker className="h-5 w-5" />}>
              <Input label="Name" value={substrateName} onChange={setSubstrateName} />
              <Input label="SMILES" value={smiles} onChange={setSmiles} mono />
              <label className="mt-3 block text-sm font-medium text-gray-700">
                Role
                <select
                  value={substrateRole}
                  onChange={(event) => setSubstrateRole(event.target.value)}
                  className="mt-2 w-full border border-gray-300 bg-[#fbfbf8] px-3 py-2 text-black outline-none focus:border-[#5BA8B9]"
                >
                  {['substrate', 'product', 'inhibitor', 'analog'].map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </label>
              <ActionButton onClick={saveSubstrate} disabled={!currentProjectId} icon={<Save className="h-4 w-4" />}>
                Save substrate
              </ActionButton>
              <RecordList items={project?.substrates.map((item) => `${item.name} (${item.role})`) ?? []} />
            </Panel>
          </aside>

          <main className="space-y-6">
            <div className="grid gap-6 xl:grid-cols-2">
              <Panel title="Protein sequence" icon={<FileText className="h-5 w-5" />}>
                <textarea
                  value={sequence}
                  onChange={(event) => setSequence(event.target.value)}
                  className="min-h-[220px] w-full resize-y border border-gray-300 bg-[#fbfbf8] p-4 font-mono text-xs outline-none focus:border-[#5BA8B9]"
                  spellCheck={false}
                />
                <ActionButton onClick={saveSequence} disabled={!currentProjectId} icon={<Activity className="h-4 w-4" />}>
                  Validate sequence
                </ActionButton>
                {project?.sequence?.feature_json && (
                  <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                    <Metric label="Length" value={`${project.sequence.sequence_length} aa`} />
                    <Metric label="MW" value={project.sequence.molecular_weight?.toFixed(1) ?? 'n/a'} />
                    <Metric label="pI" value={project.sequence.pI?.toFixed(2) ?? 'n/a'} />
                    <Metric label="Instability" value={project.sequence.instability_index?.toFixed(2) ?? 'n/a'} />
                    <Metric label="GRAVY" value={project.sequence.GRAVY?.toFixed(2) ?? 'n/a'} />
                    <Metric label="Aromaticity" value={project.sequence.aromaticity?.toFixed(2) ?? 'n/a'} />
                  </dl>
                )}
              </Panel>

              <Panel title="Structure input" icon={<Box className="h-5 w-5" />}>
                <div className="grid grid-cols-[minmax(0,1fr)_auto_90px] items-end gap-3">
                  <Input label="PDB ID" value={pdbId} onChange={setPdbId} mono />
                  <button
                    type="button"
                    onClick={fetchPdb}
                    className="border border-gray-900 px-4 py-2 text-sm font-medium transition hover:border-[#5BA8B9] hover:text-[#5BA8B9]"
                  >
                    Fetch
                  </button>
                  <Input label="Chain" value={chainId} onChange={setChainId} />
                </div>
                <textarea
                  value={pdbText}
                  onChange={(event) => setPdbText(event.target.value)}
                  className="mt-3 min-h-[220px] w-full resize-y border border-gray-300 bg-[#fbfbf8] p-4 font-mono text-xs outline-none focus:border-[#5BA8B9]"
                  spellCheck={false}
                />
                <ActionButton onClick={saveStructure} disabled={!currentProjectId} icon={<Save className="h-4 w-4" />}>
                  Save PDB
                </ActionButton>
              </Panel>
            </div>

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
              <Panel title="3D structure viewer" icon={<FlaskConical className="h-5 w-5" />}>
                <PdbViewer structure={activeStructure} activeSites={project?.active_sites ?? []} />
              </Panel>

              <Panel title="Active site" icon={<Activity className="h-5 w-5" />}>
                <Input label="Residues" value={activeSite} onChange={setActiveSite} mono />
                <ActionButton onClick={saveActiveSite} disabled={!currentProjectId || !activeStructure} icon={<Save className="h-4 w-4" />}>
                  Save active site
                </ActionButton>
                <RecordList items={project?.active_sites.map((item) => `${item.name}: ${item.residue_list.join(', ')}`) ?? []} />
                {project?.active_sites[0] && (
                  <div className="mt-4 space-y-3 text-sm">
                    <ResidueGroup label="Nearby 4-8 A context" items={project.active_sites[0].nearby_residues} />
                    <ResidueGroup label="Mutation candidates" items={project.active_sites[0].mutation_candidate_residues} />
                    <ResidueGroup label="Do not mutate" items={project.active_sites[0].protected_residues} />
                  </div>
                )}
              </Panel>
            </div>

            <Panel title="Variant prioritization" icon={<GitBranch className="h-5 w-5" />}>
              <div className="flex flex-wrap gap-3">
                <ActionButton onClick={generateVariants} disabled={!currentProjectId || !project?.sequence} icon={<GitBranch className="h-4 w-4" />}>
                  Generate variants
                </ActionButton>
                <ActionButton onClick={generateReport} disabled={!currentProjectId} icon={<FileText className="h-4 w-4" />}>
                  Generate memo
                </ActionButton>
              </div>
              <div className="mt-5 overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-gray-200 text-xs uppercase text-gray-500">
                    <tr>
                      <th className="py-3 pr-4">Mutation</th>
                      <th className="py-3 pr-4">Final</th>
                      <th className="py-3 pr-4">Active site</th>
                      <th className="py-3 pr-4">Risk</th>
                      <th className="py-3 pr-4">Explanation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {variants.map((variant) => (
                      <tr key={variant.id} className="border-b border-gray-100 align-top">
                        <td className="py-3 pr-4 font-mono">{variant.mutation_label}</td>
                        <td className="py-3 pr-4">{variant.final_score?.toFixed(2)}</td>
                        <td className="py-3 pr-4">{variant.active_site_relevance_score?.toFixed(2)}</td>
                        <td className="py-3 pr-4">{variant.mutation_risk_score?.toFixed(2)}</td>
                        <td className="max-w-xl py-3 pr-4 text-gray-700">{variant.explanation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {report && (
                <pre className="mt-5 max-h-[420px] overflow-auto whitespace-pre-wrap bg-[#081e24] p-5 text-sm leading-relaxed text-gray-100">
                  {report.markdown_report}
                </pre>
              )}
            </Panel>
          </main>
        </div>
      </div>
    </div>
  );
}

function PdbViewer({ structure, activeSites }: { structure: EnzymeStructureRecord | null; activeSites: ActiveSiteRecord[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (window.$3Dmol) {
      setReady(true);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://3dmol.org/build/3Dmol-min.js';
    script.async = true;
    script.onload = () => setReady(true);
    script.onerror = () => setError('3Dmol.js could not be loaded.');
    document.body.appendChild(script);
  }, []);

  useEffect(() => {
    if (!ready || !ref.current || !structure?.raw_pdb_text || !window.$3Dmol) return;
    try {
      ref.current.innerHTML = '';
      const viewer = window.$3Dmol.createViewer(ref.current, { backgroundColor: '#ffffff' });
      viewer.addModel(structure.raw_pdb_text, 'pdb');
      viewer.setStyle({}, { cartoon: { color: 'spectrum' } });
      activeSites.forEach((site) => {
        viewer.addStyle({ resi: site.residue_positions }, { stick: { color: 'yellow', radius: 0.18 } });
      });
      viewer.zoomTo();
      viewer.render();
      setError(null);
    } catch {
      setError('Structure could not be rendered from the provided PDB text.');
    }
  }, [activeSites, ready, structure]);

  if (!structure?.raw_pdb_text) {
    return <div className="flex h-[420px] items-center justify-center border border-dashed border-gray-300 text-sm text-gray-500">Save PDB text to render the structure.</div>;
  }

  return (
    <div className="space-y-3">
      <div ref={ref} className="h-[420px] w-full border border-gray-200 bg-white" />
      {error && <p className="text-sm text-rose-700">{error}</p>}
      <p className="text-xs leading-relaxed text-gray-500">
        Active-site residues are highlighted when residue numbers match the provided PDB.
      </p>
    </div>
  );
}

function Panel({ title, icon, children }: { title: string; icon: ReactNode; children: ReactNode }) {
  return (
    <section className="border border-gray-300 bg-white p-5">
      <div className="mb-4 flex items-center gap-3">
        <span className="text-[#5BA8B9]">{icon}</span>
        <h2 className="font-serif text-xl font-semibold">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Input({ label, value, onChange, mono, hidden }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  mono?: boolean;
  hidden?: boolean;
}) {
  if (hidden) return <span className="sr-only">{label}</span>;
  return (
    <label className="block text-sm font-medium text-gray-700">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={`mt-2 w-full border border-gray-300 bg-[#fbfbf8] px-3 py-2 text-black outline-none focus:border-[#5BA8B9] ${mono ? 'font-mono text-xs' : 'text-sm'}`}
      />
    </label>
  );
}

function ActionButton({ children, icon, disabled, onClick }: {
  children: ReactNode;
  icon: ReactNode;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="mt-4 inline-flex items-center gap-2 border border-black px-4 py-2 text-sm font-medium transition hover:border-[#5BA8B9] hover:text-[#5BA8B9] disabled:cursor-not-allowed disabled:opacity-50"
    >
      {icon}
      {children}
    </button>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-gray-200 bg-[#fbfbf8] p-3">
      <dt className="text-xs uppercase tracking-wide text-gray-500">{label}</dt>
      <dd className="mt-1 font-medium text-gray-900">{value}</dd>
    </div>
  );
}

function RecordList({ items }: { items: string[] }) {
  if (!items.length) return <p className="mt-4 text-sm text-gray-500">No records yet.</p>;
  return (
    <ul className="mt-4 space-y-2 text-sm text-gray-700">
      {items.map((item) => (
        <li key={item} className="border border-gray-200 bg-[#fbfbf8] px-3 py-2">{item}</li>
      ))}
    </ul>
  );
}

function ResidueGroup({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="border border-gray-200 bg-[#fbfbf8] p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-2 font-mono text-xs text-gray-800">
        {items.length ? items.join(', ') : 'n/a'}
      </p>
    </div>
  );
}

function StatusBadge({ status, error }: { status: string; error: string | null }) {
  return (
    <div className={`max-w-md border px-4 py-3 text-sm ${error ? 'border-rose-300 bg-rose-50 text-rose-800' : 'border-gray-300 bg-white text-gray-700'}`}>
      {error ?? status}
    </div>
  );
}
