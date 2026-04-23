import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatDockingScore(score: number): string {
  return `${score.toFixed(1)} kcal/mol`;
}

export function getDockingScoreColor(score: number): string {
  if (score <= -7) return 'text-emerald-600';
  if (score <= -5) return 'text-amber-600';
  return 'text-rose-600';
}

export function getDockingScoreBg(score: number): string {
  if (score <= -7) return 'bg-emerald-50';
  if (score <= -5) return 'bg-amber-50';
  return 'bg-rose-50';
}

export function getPubChemImageUrl(cid: string): string {
  return `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/PNG`;
}

export function getPdbUrl(pdbId: string): string {
  return `https://files.rcsb.org/download/${pdbId}.pdb`;
}

export function getAlphaFoldUrl(alphafoldId: string): string {
  return `https://alphafold.ebi.ac.uk/entry/${alphafoldId}`;
}

export function getPubChemLink(cid: string): string {
  return `https://pubchem.ncbi.nlm.nih.gov/compound/${cid}`;
}
