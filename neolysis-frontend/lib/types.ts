export type Disease = 'leptospirosis' | 'scrub-typhus' | 'melioidosis' | 'dengue';

export interface ProteinTarget {
  id: string;
  name: string;
  fullName: string;
  disease: Disease;
  organism: string;
  description: string;
  pdbId: string;
  alphafoldId: string;
  uniprotId: string;
  candidateCount: number;
  bindingSiteDescription: string;
}

export interface Compound {
  cid: string;
  name: string;
  iupacName: string;
  formula: string;
  smiles: string;
  mw: number;
  logP: number;
  hbd: number;
  hba: number;
  tpsa: number;
  rotBonds: number;
  lipinskiPass: boolean;
}

export interface DockingScore {
  compoundCid: string;
  targetId: string;
  score: number;
  computedAt: string;
}

export interface AIInsight {
  targetId: string;
  compoundCid: string;
  whyTargetMatters: string;
  whyCompoundPromising: string;
  researchGap: string;
  generatedAt: string;
}

export interface CompoundWithDocking extends Compound {
  dockingScore: number;
  targetId: string;
  ligandEfficiency?: number;
  confidence?: number;
  explanation?: string;
}

export const DISEASE_COLORS: Record<Disease, { bg: string; text: string; border: string }> = {
  leptospirosis: { bg: 'bg-teal-100', text: 'text-teal-800', border: 'border-teal-200' },
  'scrub-typhus': { bg: 'bg-amber-100', text: 'text-amber-800', border: 'border-amber-200' },
  melioidosis: { bg: 'bg-purple-100', text: 'text-purple-800', border: 'border-purple-200' },
  dengue: { bg: 'bg-rose-100', text: 'text-rose-800', border: 'border-rose-200' },
};

export const DISEASE_LABELS: Record<Disease, string> = {
  leptospirosis: 'Leptospirosis',
  'scrub-typhus': 'Scrub Typhus',
  melioidosis: 'Melioidosis',
  dengue: 'Dengue',
};

export interface DockingCSVResult {
  target: string;
  pocket: number;
  cid: number;
  name: string;
  smiles: string;
  mw: number;
  logp: number;
  affinity: number;
  ligand_eff: number;
  affinity_rank: number;
  le_rank: number;
  composite: number;
  confidence: number;
  explanation?: string;
}

export interface CompoundWithDockingCSV extends DockingCSVResult {
  dockingScore: number;
  ligandEfficiency: number;
  targetId: string;
}
