import { VariantCandidate } from '@/lib/enzyme-api';

const PROTEIN_SEQUENCE_PATTERN = /^[ACDEFGHIKLMNPQRSTVWY]{30,}$/i;

export function parseVariantInput(text: string): VariantCandidate[] {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map(parseVariantLine);
}

function parseVariantLine(line: string, index: number): VariantCandidate {
  const colonIndex = line.indexOf(':');
  const idPart = colonIndex >= 0 ? line.slice(0, colonIndex) : `V${index + 1}`;
  const value = (colonIndex >= 0 ? line.slice(colonIndex + 1) : line).trim();

  if (PROTEIN_SEQUENCE_PATTERN.test(value)) {
    return {
      variant_id: idPart.trim(),
      sequence: value.toUpperCase(),
    };
  }

  return {
    variant_id: idPart.trim(),
    mutations: value
      .split(/[,\s]+/)
      .map((item) => item.trim())
      .filter(Boolean),
  };
}
