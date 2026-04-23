import fs from 'fs';
import path from 'path';
import { CompoundWithDocking } from './types';

/**
 * Map CSV target names → frontend target IDs.
 * CSV uses protein names; our frontend uses slug IDs.
 */
const CSV_TARGET_TO_ID: Record<string, string> = {
  'LipL32': 'lipl32',
  'LenA': 'lena',
  'ScaC': 'scac',
  'OmpA': 'ompa',
  'BimA': 'bima',
  'BpeB': 'bohA',          // BpeB is B. pseudomallei efflux pump → mapped to melioidosis target
  'NS3_Helicase': 'ns2b-ns3',
};

interface CSVRow {
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
  explanation: string;
}

/**
 * Parse a CSV line that may contain quoted fields with commas inside.
 */
function parseCSVLine(line: string): string[] {
  const fields: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && i + 1 < line.length && line[i + 1] === '"') {
        current += '"';
        i++; // skip escaped quote
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      fields.push(current.trim());
      current = '';
    } else {
      current += ch;
    }
  }
  fields.push(current.trim());
  return fields;
}

/**
 * Lipinski Rule of Five check.
 */
function checkLipinski(mw: number, logp: number, hbd: number, hba: number): boolean {
  return mw <= 500 && logp <= 5 && hbd <= 5 && hba <= 10;
}

/**
 * Estimate HBD (hydrogen-bond donors) from SMILES.
 * Counts OH and NH patterns as a rough heuristic.
 */
function estimateHBD(smiles: string): number {
  const ohMatches = smiles.match(/O(?=[^=])|O$/g) || [];
  const nhMatches = smiles.match(/N(?=[^=+\-])|N$/g) || [];
  // Very rough: count O not in C=O, N not in N= patterns
  return Math.min(ohMatches.length, 5) + Math.min(nhMatches.length, 3);
}

/**
 * Estimate HBA (hydrogen-bond acceptors) from SMILES.
 * Counts N and O atoms.
 */
function estimateHBA(smiles: string): number {
  const oCount = (smiles.match(/O/g) || []).length;
  const nCount = (smiles.match(/N/g) || []).length;
  return oCount + nCount;
}

let _cachedRows: CSVRow[] | null = null;

function loadCSVData(): CSVRow[] {
  if (_cachedRows) return _cachedRows;

  const csvPath = path.join(process.cwd(), 'public', 'data', 'top10_per_pocket.csv');
  const raw = fs.readFileSync(csvPath, 'utf-8');
  const lines = raw.split('\n').filter((l) => l.trim().length > 0);

  // Skip header
  const rows: CSVRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const fields = parseCSVLine(lines[i]);
    if (fields.length < 14) continue;

    rows.push({
      target: fields[0],
      pocket: parseInt(fields[1], 10),
      cid: parseInt(fields[2], 10),
      name: fields[3],
      smiles: fields[4],
      mw: parseFloat(fields[5]),
      logp: parseFloat(fields[6]),
      affinity: parseFloat(fields[7]),
      ligand_eff: parseFloat(fields[8]),
      affinity_rank: parseFloat(fields[9]),
      le_rank: parseFloat(fields[10]),
      composite: parseFloat(fields[11]),
      confidence: parseFloat(fields[12]),
      explanation: fields[13] || '',
    });
  }

  _cachedRows = rows;
  return rows;
}

/**
 * Get all compounds with docking data for a specific target ID.
 * Returns them sorted by affinity (most negative = strongest binding first).
 */
const PUBCHEM_PROPS: Record<string, { tpsa: number; rotBonds: number }> = {
  "5379": {"tpsa": 82.1, "rotBonds": 4}, "6713992": {"tpsa": 144, "rotBonds": 3}, "54678924": {"tpsa": 158, "rotBonds": 1}, 
  "56206": {"tpsa": 64.1, "rotBonds": 3}, "56208": {"tpsa": 72.9, "rotBonds": 3}, "58258": {"tpsa": 89.4, "rotBonds": 2}, 
  "2962711": {"tpsa": 150, "rotBonds": 6}, "100252": {"tpsa": 190, "rotBonds": 5}, "3357": {"tpsa": 64.1, "rotBonds": 4}, 
  "4658465": {"tpsa": 107, "rotBonds": 4}, "65958": {"tpsa": 82.1, "rotBonds": 5}, "10489511": {"tpsa": 123, "rotBonds": 3}, 
  "71335": {"tpsa": 64.1, "rotBonds": 3}, "3374": {"tpsa": 57.6, "rotBonds": 1}, "60464": {"tpsa": 98.9, "rotBonds": 3}, 
  "54681908": {"tpsa": 174, "rotBonds": 5}, "4410": {"tpsa": 81.1, "rotBonds": 2}, "60605": {"tpsa": 72.9, "rotBonds": 3}, 
  "321727": {"tpsa": 190, "rotBonds": 5}, "92099": {"tpsa": 115, "rotBonds": 5}, "45273159": {"tpsa": 169, "rotBonds": 6}, 
  "498376": {"tpsa": 139, "rotBonds": 3}, "54675783": {"tpsa": 165, "rotBonds": 3}, "5064": {"tpsa": 144, "rotBonds": 3}, 
  "2764": {"tpsa": 72.9, "rotBonds": 3}, "3006933": {"tpsa": 145, "rotBonds": 3}, "5046881": {"tpsa": 95.2, "rotBonds": 4}, 
  "44392548": {"tpsa": 159, "rotBonds": 5}, "3647975": {"tpsa": 132, "rotBonds": 6}, "3948": {"tpsa": 72.9, "rotBonds": 3}, 
  "10070893": {"tpsa": 115, "rotBonds": 16}, "60021": {"tpsa": 72.9, "rotBonds": 3}, "10633086": {"tpsa": 123, "rotBonds": 2}
};

export function getCompoundsWithDockingForTarget(targetId: string): CompoundWithDocking[] {
  const rows = loadCSVData();

  // Find which CSV target name maps to this ID
  const csvTargetName = Object.entries(CSV_TARGET_TO_ID).find(
    ([, id]) => id === targetId
  )?.[0];

  if (!csvTargetName) return [];

  return rows
    .filter((r) => r.target === csvTargetName)
    .map((r) => {
      const hbd = estimateHBD(r.smiles);
      const hba = estimateHBA(r.smiles);
      const props = PUBCHEM_PROPS[String(r.cid)] || { tpsa: 0, rotBonds: 0 };

      return {
        cid: String(r.cid),
        name: r.name,
        iupacName: r.name,
        formula: '', // Not in CSV — will be hidden in card if empty
        smiles: r.smiles,
        mw: r.mw,
        logP: r.logp,
        hbd,
        hba,
        tpsa: props.tpsa,
        rotBonds: props.rotBonds,
        lipinskiPass: checkLipinski(r.mw, r.logp, hbd, hba),
        dockingScore: r.affinity,
        targetId,
        ligandEfficiency: r.ligand_eff,
        confidence: r.confidence,
        explanation: r.explanation,
      };
    })
    .sort((a, b) => a.dockingScore - b.dockingScore);
}

/**
 * Get compound count for a target (used in target cards).
 */
export function getCompoundCountForTarget(targetId: string): number {
  return getCompoundsWithDockingForTarget(targetId).length;
}

/**
 * Get a compound by CID across all targets.
 * Returns the first match found (compound data is the same regardless of target).
 */
export function getCompoundByCid(cid: string): CompoundWithDocking | undefined {
  const rows = loadCSVData();
  const numericCid = parseInt(cid, 10);
  const row = rows.find((r) => r.cid === numericCid);
  if (!row) return undefined;

  const frontendTargetId = CSV_TARGET_TO_ID[row.target] || row.target;
  const hbd = estimateHBD(row.smiles);
  const hba = estimateHBA(row.smiles);
  const props = PUBCHEM_PROPS[String(row.cid)] || { tpsa: 0, rotBonds: 0 };

  return {
    cid: String(row.cid),
    name: row.name,
    iupacName: row.name,
    formula: '',
    smiles: row.smiles,
    mw: row.mw,
    logP: row.logp,
    hbd,
    hba,
    tpsa: props.tpsa,
    rotBonds: props.rotBonds,
    lipinskiPass: checkLipinski(row.mw, row.logp, hbd, hba),
    dockingScore: row.affinity,
    targetId: frontendTargetId,
    ligandEfficiency: row.ligand_eff,
    confidence: row.confidence,
    explanation: row.explanation,
  };
}

/**
 * Get docking score for a specific compound-target pair.
 */
export function getDockingScoreForCompound(
  cid: string,
  targetId: string
): { compoundCid: string; targetId: string; score: number; computedAt: string } | undefined {
  const rows = loadCSVData();
  const numericCid = parseInt(cid, 10);
  const csvTargetName = Object.entries(CSV_TARGET_TO_ID).find(
    ([, id]) => id === targetId
  )?.[0];

  if (!csvTargetName) return undefined;

  const row = rows.find((r) => r.cid === numericCid && r.target === csvTargetName);
  if (!row) return undefined;

  return {
    compoundCid: String(row.cid),
    targetId,
    score: row.affinity,
    computedAt: '2025-04-15', // CSV doesn't have timestamps, use a fixed date
  };
}
