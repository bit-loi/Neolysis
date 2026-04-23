import { ProteinTarget } from './types';

export const proteinTargets: ProteinTarget[] = [
  {
    id: 'lipl32',
    name: 'LipL32',
    fullName: 'Lipid-binding protein LipL32',
    disease: 'leptospirosis',
    organism: 'Leptospira interrogans',
    description: 'The most abundant outer membrane protein in pathogenic Leptospira species, highly expressed during infection and essential for host cell adhesion and invasion.',
    pdbId: '6GJ5',
    alphafoldId: 'AF-Q5IC35-F1',
    uniprotId: 'Q5IC35',
    candidateCount: 10,
    bindingSiteDescription: 'Contains a hydrophobic pocket suitable for lipid binding, critical for interaction with host extracellular matrix proteins.',
  },
/*
  {
    id: 'lena',
    name: 'LenA',
    fullName: 'Leptospiral endostatin-like protein A',
    disease: 'leptospirosis',
    organism: 'Leptospira interrogans',
    description: 'An alpha-helical protein that binds fibronectin and laminin, facilitating tissue colonization and dissemination during infection.',
    pdbId: '3H7T',
    alphafoldId: 'AF-Q72Q00-F1',
    uniprotId: 'Q72Q00',
    candidateCount: 0,
    bindingSiteDescription: 'Surface-exposed region with fibronectin-binding activity, target for neutralizing antibody development.',
  },
*/
  {
    id: 'scac',
    name: 'ScaC',
    fullName: 'Surface cell antigen 2',
    disease: 'scrub-typhus',
    organism: 'Orientia tsutsugamushi',
    description: 'A major surface-exposed protein involved in host cell attachment and invasion, making it a prime target for vaccine development.',
    pdbId: '6VXX',
    alphafoldId: 'AF-A0A2H4T4F0-F1',
    uniprotId: 'A0A2H4T4F0',
    candidateCount: 10,
    bindingSiteDescription: 'Hypervariable region involved in immune evasion and host cell tropism determination.',
  },
/*
  {
    id: 'ompa',
    name: 'OmpA',
    fullName: 'Outer membrane protein A',
    disease: 'scrub-typhus',
    organism: 'Orientia tsutsugamushi',
    description: 'Conserved outer membrane protein essential for structural integrity and involved in adhesion to host cells during scrub typhus infection.',
    pdbId: '7B8Y',
    alphafoldId: 'AF-Q9ZDN5-F1',
    uniprotId: 'Q9ZDN5',
    candidateCount: 0,
    bindingSiteDescription: 'Beta-barrel structure with extracellular loops suitable for small molecule inhibitor targeting.',
  },
  {
    id: 'bima',
    name: 'BimA',
    fullName: 'Biofilm formation protein BimA',
    disease: 'melioidosis',
    organism: 'Burkholderia pseudomallei',
    description: 'Critical for actin-based motility and cell-to-cell spread, enabling bacterial dissemination within the host.',
    pdbId: '6JWP',
    alphafoldId: 'AF-Q63JP8-F1',
    uniprotId: 'Q63JP8',
    candidateCount: 0,
    bindingSiteDescription: 'ATP-binding site critical for actin polymerization activity, essential for virulence.',
  },
  {
    id: 'bohA',
    name: 'BopA',
    fullName: 'Autophagy inhibitor BopA',
    disease: 'melioidosis',
    organism: 'Burkholderia pseudomallei',
    description: 'Secreted effector protein that inhibits host autophagy, enabling bacterial survival within phagosomes.',
    pdbId: '6V6P',
    alphafoldId: 'AF-Q63K96-F1',
    uniprotId: 'Q63K96',
    candidateCount: 10,
    bindingSiteDescription: 'Critical domain for PI3K interaction and autophagy inhibition, potential antiviral-like mechanism targeting.',
  },
*/
  {
    id: 'ns2b-ns3',
    name: 'NS2B-NS3',
    fullName: 'NS2B-NS3 protease complex',
    disease: 'dengue',
    organism: 'Dengue virus',
    description: 'Essential viral protease complex responsible for polyprotein processing, critical for viral replication and a well-validated drug target.',
    pdbId: '6M17',
    alphafoldId: 'AF-P29990-F1',
    uniprotId: 'P29990',
    candidateCount: 10,
    bindingSiteDescription: 'Shallow catalytic cleft at the NS2B-NS3 interface, challenging but tractable for inhibitor design.',
  },
];

export function getTargetById(id: string): ProteinTarget | undefined {
  return proteinTargets.find((target) => target.id === id);
}

export function getTargetsByDisease(disease: string): ProteinTarget[] {
  if (disease === 'all') return proteinTargets;
  return proteinTargets.filter((target) => target.disease === disease);
}
